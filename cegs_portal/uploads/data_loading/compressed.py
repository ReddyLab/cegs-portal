import os.path
import tarfile
import tempfile

from .analysis import Analysis
from .experiment import Experiment
from .metadata import AnalysisMetadata, ExperimentMetadata


def load(compressed_file, experiment_accession_id):
    with tarfile.open(fileobj=compressed_file, mode="r:gz") as data_files, tempfile.TemporaryDirectory() as dir_name:
        data_files.extractall(dir_name)

        experiment_filename = os.path.join(dir_name, "experiment.json")
        expr_data_filename = os.path.join(dir_name, "tested_elements.tsv")
        analysis_filename = os.path.join(dir_name, "analysis001.json")
        analysis_data_filename = os.path.join(dir_name, "observations.tsv")

        metadata = ExperimentMetadata.load(experiment_filename, experiment_accession_id)
        Experiment(metadata).load(expr_data_filename).save()

        metadata = AnalysisMetadata.load(analysis_filename, experiment_accession_id)
        analysis = Analysis(metadata).load(analysis_data_filename).save()
        return analysis.accession_id
