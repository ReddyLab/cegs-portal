import logging
import traceback

from django.db import connection
from huey.contrib.djhuey import db_task

from cegs_portal.utils.decorators import skip_receiver_in_testing


@skip_receiver_in_testing
@db_task()
def update_experiment_access(experiment, created):
    if created:
        return

    logger = logging.getLogger(__name__)
    logger.info(f"{experiment.accession_id} Updating Experiment Access")
    traceback.print_stack()

    with connection.cursor() as cursor:
        cursor.execute(
            """UPDATE search_analysis
               SET public = %s, archived = %s
               WHERE experiment_accession_id = %s""",
            [experiment.public, experiment.archived, experiment.accession_id],
        )
        cursor.execute(
            """UPDATE search_dnafeature
               SET public = %s, archived = %s
               WHERE experiment_accession_id = %s""",
            [experiment.public, experiment.archived, experiment.accession_id],
        )
        cursor.execute(
            """UPDATE search_regulatoryeffectobservation
               SET public = %s, archived = %s
               WHERE experiment_accession_id = %s""",
            [experiment.public, experiment.archived, experiment.accession_id],
        )


@skip_receiver_in_testing
@db_task()
def update_analysis_access(analysis, created):
    if created:
        return

    with connection.cursor() as cursor:
        cursor.execute(
            """UPDATE search_regulatoryeffectobservation
               SET public = %s, archived = %s
               WHERE analysis_accession_id = %s""",
            [analysis.public, analysis.archived, analysis.accession_id],
        )
