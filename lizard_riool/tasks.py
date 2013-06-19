import logging
import os
import time
import traceback

from celery.task import task
from celery.result import AsyncResult

from django.core.cache import cache
from django.db import transaction

from lizard_riool import datamodel
from lizard_riool import models
from lizard_riool import save_uploaded_data

logger = logging.getLogger(__name__)

# Implement a simple lock using memcached

# The cache really isn't the best for this sort of thing, but it's
# simple, and the Celery manual actually recommends it:
# http://docs.celeryproject.org/en/latest/cookbook/tasks.html# \
# ensuring-a-task-is-only-executed-one-at-a-time

LOCK_KEY = "lizard_riool_computing_all_lost_capacity_percentages"
DURATION = 60 * 60  # If something happens, we want computing to be
                    # possible again after 60 minutes. In testing, the
                    # computation only takes around 10 minutes.

MAX_RETRIES = 5


@task
def process_uploaded_file_when_ready(upload_id, retries=MAX_RETRIES):
    if retries <= 0:
        return  # Forget it
    try:
        upload = models.Upload.objects.get(pk=upload_id)
    except models.Upload.DoesNotExist:
        time.sleep(1)  # Wait one second, then try again
        process_uploaded_file_when_ready.delay(upload_id, retries - 1)
        return

    if not os.path.exists(upload.full_path):
        time.sleep(1)  # Wait one second, then try again
        process_uploaded_file_when_ready.delay(upload_id, retries - 1)
        return

    process_uploaded_file.delay(upload)


@task
def process_uploaded_file(upload):
    # If it's an RIB, ignore it, otherwise it's an RMB -- find its RIB.
    if upload.suffix.lower() != ".rmb":
        return

    # Set "being processed" status
    upload.set_being_processed()

    rib = upload.find_relevant_rib()

    if not rib:
        upload.record_error("Bijbehorende RIB file niet gevonden.")
        upload.set_unsuccessful()
        return

    rib.set_being_processed()

    sewerage_name = os.path.basename(upload.the_file)[:-4]  # Minus ".RMB"

    if models.Sewerage.objects.filter(name=sewerage_name).exists():
        upload.record_error(
            ("Er bestaat al een stelsel met de naam '{name}'. "
             "Verwijder het op de archiefpagina, of gebruik "
             "een andere naam.").format(name=sewerage_name))
        upload.set_unsuccessful()
        rib.set_unsuccessful()
        return

    for other_upload in models.Upload.objects.filter(status=2):
        if other_upload == upload or other_upload == rib:
            continue
        if other_upload.filename.lower() == upload.filename.lower():
            upload.record_error(
                ("Er wordt al een bestand met de naam '{name}' verwerkt. "
                 ).format(name=upload.filename))
            upload.set_unsuccessful()
            rib.set_unsuccessful()
            return

    try:
        with transaction.commit_on_success():
            # All the actual processing
            save_uploaded_data.protected_file_processing(rib, upload)

    except Exception as e:
        # Record whatever happened
        error_message = (
            "Exception: {e} {t}"
            .format(e=e, t=traceback.format_exc()[-250:]))
        upload.record_error(error_message)
        rib.record_error(error_message)
        upload.set_unsuccessful()
        rib.set_unsuccessful()


@task
def compute_all_lost_capacity_percentages():
    """Call compute_flooded_percentages() on all RMB files. The function
    will return without doing anything if the computation was already done
    before. Wrap everything in a transaction to ensure that files are either
    completely computed or not at all.

    This function should usually be called using
    lizard_riool.tasks.compute_lost_capacity_async, which also
    implements locking.
    """

    logger.debug("Starting compute_all_lost_capacity_percentages Task")

    for f in models.Upload.objects.filter(the_file__iendswith='.rmb'):
        if not f.has_computed_percentages:
            with transaction.commit_on_success():
                rmb = datamodel.RMB(f)
                rmb.compute_flooded_percentages()


def compute_lost_capacity_async():
    """Uses Celery to call the compute_all_lost_capacity_percentages
    task.

    If the task is already running (according to the cache) but not
    yet successful, nothing happens and the old task is returned.

    Otherwise, a new task is started, its task_id is cached and the
    task is returned.

    Using the cache for locking isn't ideal, but in my defense, it's
    also what they recommend in the Cookbook section of the Celery
    manual. It forces the cache to be shared between all instances of
    this site and isn't sufficiently persistent.

    If two threads are both trying to start up the task, it's possible
    that this thread is blocked but the task isn't known yet. In that
    case, the function returns None."""

    task_id = cache.get(LOCK_KEY)

    if task_id is not None:
        if task_id == 'pending':
            # Another task is starting, we don't have to
            return None

        logger.debug("found task_id: %s" % (task_id,))
        result = AsyncResult(task_id)
        logger.debug("task state is %s." % (result.state,))

        if not result.ready():
            # We're still busy
            return result
        elif not result.successful():
            logger.critical(
                "lost capacity task finished with an exception: %s" %
                (str(result.result),))
        cache.delete(LOCK_KEY)

    else:
        logger.debug("found no task_id.")

    # Now, as far as we know, the cache is empty
    if not cache.add(LOCK_KEY, 'pending'):
        # If add() returns False, the key already exists -- some other thread
        # also added it.
        return

    task = compute_all_lost_capacity_percentages.delay()
    cache.set(LOCK_KEY, task.task_id, DURATION)
    logger.debug("made a new task with id %s." % task.task_id)

    return task
