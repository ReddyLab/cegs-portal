from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver

from cegs_portal.search.models.experiment import Experiment
from cegs_portal.tasks.decorators import as_task
from cegs_portal.utils.decorators import skip_receiver_in_testing


@receiver(post_save, sender=Experiment)
@skip_receiver_in_testing
@as_task(pass_task=True)
def set_access_controls(task, sender, instance, created, raw, using, update_fields, **kwargs):
    """This reciever is run when access permissions are changed on an experiment. It updates
    the access permissions on the dna features and REOs associated with the experiment.

    :param task_id: The id of the ThreadTask associated with this thread.
    :type task_id: int

    The other paramaters all have to do with django signal recievers.
    """
    if created:
        task.set_description("Experiment created")
        return

    task.set_description(f"Modify access controls of {instance.accession_id}")

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
