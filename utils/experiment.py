import json


class ExperimentData:
    WGCERES_DATA = "wgceres"

    def __init__(self, ref_genome, ref_genome_patch, cell_line, filename, datatype):
        self.ref_genome = ref_genome
        self.ref_genome_patch = ref_genome_patch
        self.cell_line = cell_line
        self.filename = filename
        if datatype.lower() == self.WGCERES_DATA:
            self.datatype = self.WGCERES_DATA


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
                )
            )

    @classmethod
    def json_load(self, file):
        experiment_data = json.load(file)
        return ExperimentFile(experiment_data)
