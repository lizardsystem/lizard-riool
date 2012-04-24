from celery.task import task
from django.core.cache import cache

import lizard_riool.datamodel

# Implement a simple lock using memcached

# The cache really isn't the best for this sort of thing, but it's
# simple, and the Celery manual actually recommends it:
# http://docs.celeryproject.org/en/latest/cookbook/tasks.html# \
# ensuring-a-task-is-only-executed-one-at-a-time

LOCK_KEY = "lizard_riool_computing_all_lost_capacity_percentages"
DURATION = 10*60  # If something happens, we want computing to be
                  # possible again after 10 minutes. In testing, the
                  # computation only takes around 1 minute.

@task
def compute_all_lost_capacity_percentages():
    if cache.get(LOCK_KEY) is not None:
        # Apparently we're already working on it
        return

    cache.set(LOCK_KEY, "working on it", DURATION)
    lizard_riool.datamodel.compute_all_flooded_percentages()
    cache.delete(LOCK_KEY)
