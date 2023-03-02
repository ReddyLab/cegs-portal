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
    ExperimentDataFileInfo,
    TissueType,
)

from .file import FileMetadata
from .misc import get_delimiter


class ExperimentFileMetadata:
    file_metadata: FileMetadata
    ref_genome: str
    ref_genome_patch: str
    significance_measure: str
    p_val_threshold: float

    def __init__(self, file_metadata: dict[str, str]):
        self.file_metadata = FileMetadata(file_metadata)
        self.ref_genome = file_metadata["ref_genome"]
        self.ref_genome_patch = file_metadata.get("ref_genome_patch", None)
        self.significance_measure = file_metadata["significance_measure"]
        self.p_val_threshold = file_metadata.get("p_val_threshold", 0.05)

    def db_save(self, experiment: Experiment):
        self.file_metadata.db_save(experiment)

        data_file_info = ExperimentDataFileInfo(
            ref_genome=self.ref_genome,
            ref_genome_patch=self.ref_genome_patch,
            significance_measure=self.significance_measure,
            p_value_threshold=self.p_val_threshold,
        )
        data_file_info.save()


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
    file_metadata: list[ExperimentFileMetadata]
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
        self.file_metadata = []
        self.other_file_metadata = []
        self.biosamples = [ExperimentBiosample(sample, self) for sample in experiment_dict["biosamples"]]
        for data in experiment_dict["data"]:
            self.file_metadata.append(ExperimentFileMetadata(data))
        for file in experiment_dict.get("other_files", []):
            self.other_file_metadata.append(FileMetadata(file))

    def db_save(self):
        experiment = Experiment(
            name=self.name,
            accession_id=self.accession_id,
            description=self.description,
            experiment_type=self.experiment_type,
        )
        experiment.save()
        for metadata in self.file_metadata:
            metadata.db_save(experiment)
        for file in self.other_file_metadata:
            file.db_save(experiment)
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
        for file in experiment.files.all():
            for data in file.data_file_info.all():
                data.delete()
            file.delete()
        experiment.delete()

    def metadata(self):
        base_path = os.path.dirname(self.filename)
        for metadata in self.file_metadata:
            delimiter = get_delimiter(metadata.filename)
            data_file = open(os.path.join(base_path, metadata.filename), "r", newline="")
            yield data_file, metadata, delimiter
            data_file.close()

    @classmethod
    def json_load(cls, file: IO):
        experiment_data = json.load(file)
        metadata = ExperimentMetadata(experiment_data, file.name)
        return metadata
