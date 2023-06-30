import logging

from django.db import connection
from django.db.models.signals import post_save
from django.dispatch import receiver
from huey.contrib.djhuey import db_task

from cegs_portal.search.models.experiment import Analysis, Experiment
from cegs_portal.utils.decorators import skip_receiver_in_testing

logger = logging.getLogger("django.task")


@receiver(post_save, sender=Experiment)
@skip_receiver_in_testing
@db_task()
def update_experiment_access(sender, instance, created, raw, using, update_fields, **kwargs):
    """This reciever is run when access permissions are changed on an experiment. It updates
    the access permissions on the dna features and REOs associated with the experiment.
    """
    if created:
        # Don't do anything if the experiment has just been created
        return

    with connection.cursor() as cursor:
        cursor.execute(
            """UPDATE search_analysis
               SET public = %s, archived = %s
               WHERE experiment_accession_id = %s""",
            [instance.public, instance.archived, instance.accession_id],
        )
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


@receiver(post_save, sender=Analysis)
@skip_receiver_in_testing
@db_task()
def update_analysis_access(sender, instance, created, raw, using, update_fields, **kwargs):
    """This reciever is run when access permissions are changed on an analysis. It updates
    the access permissions on the dna features and REOs associated with the experiment.
    """
    if created:
        # Don't do anything if the analysis has just been created
        return

    with connection.cursor() as cursor:
        cursor.execute(
            """UPDATE search_regulatoryeffectobservation
               SET public = %s, archived = %s
               WHERE analysis_accession_id = %s""",
            [instance.public, instance.archived, instance.accession_id],
        )
