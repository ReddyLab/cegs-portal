import json
import os.path
from enum import Enum
from typing import IO, Any

from cegs_portal.search.models import Experiment, ExperimentDataFile

from .file import FileMetadata
from .misc import get_delimiter


class ExperimentDataType(Enum):
    WGCERES_DATA = "wgceres"
    SCCERES_DATA = "scceres"


class ExperimentDatafileMetadata:
    ref_genome: str
    ref_genome_patch: str
    cell_line: str
    filename: str
    significance_measure: str
    datatype: ExperimentDataType

    def __init__(self, file_metadata: dict[str, str]):
        self.ref_genome = file_metadata["ref_genome"]
        self.ref_genome_patch = file_metadata["ref_genome_patch"]
        self.cell_line = file_metadata["cell_line"]
        self.filename = file_metadata["filename"]
        self.significance_measure = file_metadata["significance_measure"]
        self.datatype = ExperimentDataType(file_metadata["datatype"].lower())

    def db_save(self, experiment: Experiment):
        data_file = ExperimentDataFile(
            cell_line=self.cell_line,
            experiment=experiment,
            filename=self.filename,
            ref_genome=self.ref_genome,
            ref_genome_patch=self.ref_genome_patch,
            significance_measure=self.significance_measure,
        )
        data_file.save()
        return data_file


class ExperimentMetadata:
    name: str
    filename: str
    data_file_metadata: list[ExperimentDatafileMetadata]
    other_file_metadata: list[FileMetadata]

    def __init__(self, experiment_dict: dict[str, Any], experiment_filename: str):
        self.name = experiment_dict["name"]
        self.filename = experiment_filename
        self.data_file_metadata = []
        self.other_file_metadata = []
        for data in experiment_dict["data"]:
            self.data_file_metadata.append(ExperimentDatafileMetadata(data))
        for file in experiment_dict["other_files"]:
            self.other_file_metadata.append(FileMetadata(file, self.filename))

    def db_save(self):
        experiment = Experiment(name=self.name)
        experiment.save()
        for metadata in self.data_file_metadata:
            metadata.db_save(experiment)
        for file in self.other_file_metadata:
            other_file = file.db_save()
            experiment.other_files.add(other_file)
        return experiment

    def db_del(self):
        experiment = Experiment.objects.get(name=self.name)
        experiment.data_files.all().delete()
        experiment.delete()

    def metadata(self):
        base_path = os.path.dirname(self.filename)
        for metadata in self.data_file_metadata:
            if (
                metadata.datatype == ExperimentDataType.SCCERES_DATA
                or metadata.datatype == ExperimentDataType.WGCERES_DATA
            ):
                delimiter = get_delimiter(metadata.filename)
                ceres_file = open(os.path.join(base_path, metadata.filename), "r", newline="")
                yield ceres_file, metadata, delimiter
                ceres_file.close()

    @classmethod
    def json_load(cls, file: IO):
        experiment_data = json.load(file)
        metadata = ExperimentMetadata(experiment_data, file.name)
        return metadata
