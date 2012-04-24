from celery.task import task

import lizard_riool.datamodel

@task
def compute_all_lost_capacity_percentages():
    lizard_riool.datamodel.compute_all_flooded_percentages()
