import json
import os.path
from enum import Enum
from os import PathLike

from cegs_portal.search.models import Experiment, ExperimentDataFile

from .misc import get_delimiter


class ExperimentDataType(Enum):
    WGCERES_DATA = "wgceres"
    SCCERES_DATA = "scceres"


class ExperimentDatafileMetadata:
    def __init__(self, ref_genome, ref_genome_patch, cell_line, filename, datatype, significance_measure):
        self.ref_genome = ref_genome
        self.ref_genome_patch = ref_genome_patch
        self.cell_line = cell_line
        self.filename = filename
        self.significance_measure = significance_measure
        self.datatype = ExperimentDataType(datatype.lower())


class ExperimentMetadata:
    name: str
    filename: PathLike[str]
    file_metadata: list[ExperimentDatafileMetadata]

    def __init__(self, experiment_dict, experiment_filename):
        self.name = experiment_dict["name"]
        self.filename = experiment_filename
        self.file_metadata = []
        for data in experiment_dict["data"]:
            self.file_metadata.append(
                ExperimentDatafileMetadata(
                    ref_genome=data["ref_genome"],
                    ref_genome_patch=data["ref_genome_patch"],
                    cell_line=data["cell_line"],
                    filename=data["file"],
                    datatype=data["type"],
                    significance_measure=data["significance measure"],
                )
            )

    def db_save(self):
        experiment = Experiment(name=self.name)
        experiment.save()
        for metadata in self.file_metadata:
            data_file = ExperimentDataFile(
                cell_line=metadata.cell_line,
                experiment=experiment,
                filename=metadata.filename,
                ref_genome=metadata.ref_genome,
                ref_genome_patch=metadata.ref_genome_patch,
                significance_measure=metadata.significance_measure,
            )
            data_file.save()
            experiment.data_files.add(data_file)
        return experiment

    def db_del(self):
        experiment = Experiment.objects.get(name=self.name)
        experiment.data_files.all().delete()
        experiment.delete()

    def metadata(self):
        base_path = os.path.dirname(self.filename)
        for metadata in self.file_metadata:
            if (
                metadata.datatype == ExperimentDataType.SCCERES_DATA
                or metadata.datatype == ExperimentDataType.WGCERES_DATA
            ):
                delimiter = get_delimiter(metadata.filename)
                ceres_file = open(os.path.join(base_path, metadata.filename), "r", newline="")
                yield ceres_file, metadata, delimiter
                ceres_file.close()

    @classmethod
    def json_load(cls, file):
        experiment_data = json.load(file)
        metadata = ExperimentMetadata(experiment_data, file.name)
        return metadata
