import logging
import os.path
import tarfile
import tempfile

from .analysis import Analysis
from .experiment import Experiment
from .metadata import AnalysisMetadata, ExperimentMetadata

logger = logging.getLogger(__name__)


def load(compressed_file, experiment_accession_id):
    with tarfile.open(fileobj=compressed_file, mode="r:gz") as data_files, tempfile.TemporaryDirectory() as dir_name:
        logger.info(f"{experiment_accession_id}: Extracting compressed file")
        data_files.extractall(dir_name)

        experiment_filename = os.path.join(dir_name, "experiment.json")
        expr_data_filename = os.path.join(dir_name, "tested_elements.tsv")
        analysis_filename = os.path.join(dir_name, "analysis001.json")
        analysis_data_filename = os.path.join(dir_name, "observations.tsv")

        logger.info(f"{experiment_accession_id}: Loading experiment")
        metadata = ExperimentMetadata.load(experiment_filename, experiment_accession_id)
        metadata.db_save()
        Experiment(metadata).add_file_data_source(expr_data_filename).load().save()

        logger.info(f"{experiment_accession_id}: Loading analysis")
        metadata = AnalysisMetadata.load(analysis_filename, experiment_accession_id)
        metadata.db_save()
        analysis = Analysis(metadata).add_file_data_source(analysis_data_filename).load().save()

        logger.info(f"{experiment_accession_id}: Finished loading data")
        return analysis.accession_id
