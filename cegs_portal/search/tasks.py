from huey.contrib.djhuey import db_task

from cegs_portal.search.models import Experiment


@db_task()
def count_beans(number):
    for experiment in Experiment.objects.all():
        print(experiment.name)
    print(f"-- counted {number} beans --")
    return f"Counted {number} beans"
