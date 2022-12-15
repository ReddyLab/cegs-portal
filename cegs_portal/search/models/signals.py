from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver

from cegs_portal.search.models.experiment import Experiment
from cegs_portal.tasks.decorators import as_task
from cegs_portal.tasks.models import ThreadTask
from cegs_portal.utils.decorators import skip_receiver_in_testing


@receiver(post_save, sender=Experiment)
@skip_receiver_in_testing
@as_task(pass_id=True)
def set_access_controls(task_id, sender, instance, created, raw, using, update_fields, **kwargs):
    if created:
        ThreadTask.set_description(task_id, "Experiment created")
        return

    ThreadTask.set_description(task_id, f"Modify access controls of {instance.accession_id}")

    with connection.cursor() as cursor:
        cursor.execute(
            """UPDATE search_dnafeature
               SET public = %s, archived = %s
               WHERE experiment_accession_id = %s""",
            [instance.public, instance.archived, instance.accession_id],
        )
        cursor.execute(
            """UPDATE search_regulatoryeffectobservation
               SET public = %s, archived = %s
               WHERE experiment_accession_id = %s""",
            [instance.public, instance.archived, instance.accession_id],
        )
