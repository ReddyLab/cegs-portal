import json
from enum import Enum


class ExperimentDataType(Enum):
    WGCERES_DATA = "wgceres"
    SCCERES_DATA = "scceres"


class ExperimentData:
    def __init__(self, ref_genome, ref_genome_patch, cell_line, filename, datatype, significance_measure):
        self.ref_genome = ref_genome
        self.ref_genome_patch = ref_genome_patch
        self.cell_line = cell_line
        self.filename = filename
        self.significance_measure = significance_measure
        self.datatype = ExperimentDataType(datatype.lower())


class ExperimentFile:
    def __init__(self, experiment_dict):
        self.name = experiment_dict["name"]
        self.data = []
        for data in experiment_dict["data"]:
            self.data.append(
                ExperimentData(
                    ref_genome=data["ref_genome"],
                    ref_genome_patch=data["ref_genome_patch"],
                    cell_line=data["cell_line"],
                    filename=data["file"],
                    datatype=data["type"],
                    significance_measure=data["significance measure"],
                )
            )

    @classmethod
    def json_load(self, file):
        experiment_data = json.load(file)
        return ExperimentFile(experiment_data)
