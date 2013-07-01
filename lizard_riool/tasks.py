import logging
import os
import time
import traceback

from celery.task import task

from django.db import transaction

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
        if upload.suffix.lower() != ".rib":
            upload.record_error(
                "Alleen .RIB en .RMB bestanden kunnen verwerkt worden")
            upload.set_unsuccessful()
            return
        else:
            # Just let it wait for the .RMB
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
