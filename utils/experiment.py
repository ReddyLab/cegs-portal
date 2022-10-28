import json
import os.path
from datetime import datetime, timezone
from typing import IO, Any, TypeVar

from cegs_portal.search.conftest import experiment
from cegs_portal.search.models import (
    AccessionIdLog,
    AccessionIds,
    AccessionType,
    Biosample,
    CellLine,
    Experiment,
    ExperimentDataFile,
    TissueType,
)

from .file import FileMetadata
from .misc import get_delimiter


class ExperimentDatafileMetadata:
    description: str
    filename: str
    ref_genome: str
    ref_genome_patch: str
    significance_measure: str

    def __init__(self, file_metadata: dict[str, str]):
        self.description = file_metadata.get("description", None)
        self.filename = file_metadata["file"]
        self.ref_genome = file_metadata["ref_genome"]
        self.ref_genome_patch = file_metadata.get("ref_genome_patch", None)
        self.significance_measure = file_metadata["significance_measure"]

    def db_save(self, experiment: Experiment):
        data_file = ExperimentDataFile(
            description=self.description,
            experiment=experiment,
            filename=self.filename,
            ref_genome=self.ref_genome,
            ref_genome_patch=self.ref_genome_patch,
            significance_measure=self.significance_measure,
        )
        data_file.save()

        return data_file


T = TypeVar("T", bound="ExperimentMetadata")


class ExperimentBiosample:
    cell_line: str
    tissue_type: str
    description: str
    experiment: T

    def __init__(self, bio_metadata: dict[str, str], experiment: T):
        self.name = bio_metadata.get("name", None)
        self.description = bio_metadata.get("description", None)
        self.cell_line = bio_metadata["cell_line"]
        self.tissue_type = bio_metadata["tissue_type"]
        self.experiment = experiment

    def db_save(self):
        with AccessionIds(message=f"{experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
            cell_line = CellLine.objects.filter(name=self.cell_line).first()
            if cell_line is None:
                tissue_type, tt_created = TissueType.objects.get_or_create(name=self.tissue_type)
                if tt_created:
                    tissue_type.accession_id = accession_ids.incr(AccessionType.TT)
                    tissue_type.save()
                cell_line = CellLine(
                    name=self.cell_line,
                    accession_id=accession_ids.incr(AccessionType.CL),
                    tissue_type=tissue_type,
                    tissue_type_name=self.tissue_type,
                )
                cell_line.save()

            bios = Biosample(
                cell_line=cell_line,
                cell_line_name=cell_line.name,
                accession_id=accession_ids.incr(AccessionType.BIOS),
            )
            bios.save()


class ExperimentMetadata:
    data_file_metadata: list[ExperimentDatafileMetadata]
    description: str
    experiment_type: str
    name: str
    filename: str
    accession_id: str
    biosamples: list[ExperimentBiosample]
    other_file_metadata: list[FileMetadata]

    def __init__(self, experiment_dict: dict[str, Any], experiment_filename: str):
        self.description = experiment_dict.get("description", None)
        self.experiment_type = experiment_dict.get("type", None)
        self.name = experiment_dict["name"]
        self.accession_id = experiment_dict["accession_id"]
        self.filename = experiment_filename
        self.data_file_metadata = []
        self.other_file_metadata = []
        self.biosamples = [ExperimentBiosample(sample, self) for sample in experiment_dict["biosamples"]]
        for data in experiment_dict["data"]:
            self.data_file_metadata.append(ExperimentDatafileMetadata(data))
        for file in experiment_dict.get("other_files", []):
            self.other_file_metadata.append(FileMetadata(file, self.filename, self.experiment_type))

    def db_save(self):
        experiment = Experiment(
            name=self.name,
            accession_id=self.accession_id,
            description=self.description,
            experiment_type=self.experiment_type,
        )
        experiment.save()
        for metadata in self.data_file_metadata:
            metadata.db_save(experiment)
        for file in self.other_file_metadata:
            other_file = file.db_save()
            experiment.other_files.add(other_file)
        accession_log = AccessionIdLog(
            created_at=datetime.now(timezone.utc),
            accession_type=AccessionType.EXPERIMENT,
            accession_id=self.accession_id,
            message=self.description[:200],
        )
        accession_log.save()
        for biosample in self.biosamples:
            biosample.db_save()
        return experiment

    def db_del(self):
        experiment = Experiment.objects.get(accession_id=self.accession_id)
        experiment.data_files.all().delete()
        experiment.other_files.all().delete()
        experiment.delete()

    def metadata(self):
        base_path = os.path.dirname(self.filename)
        for metadata in self.data_file_metadata:
            delimiter = get_delimiter(metadata.filename)
            ceres_file = open(os.path.join(base_path, metadata.filename), "r", newline="")
            yield ceres_file, metadata, delimiter
            ceres_file.close()

    @classmethod
    def json_load(cls, file: IO):
        experiment_data = json.load(file)
        metadata = ExperimentMetadata(experiment_data, file.name)
        return metadata
