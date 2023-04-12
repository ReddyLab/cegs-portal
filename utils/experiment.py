import json
import os.path
from datetime import datetime, timezone
from typing import IO, Any, Optional, TypeVar

from cegs_portal.search.models import (
    AccessionIdLog,
    AccessionIds,
    AccessionType,
    Analysis,
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

    def db_save(self, experiment: Experiment, analysis: Analysis = None):
        data_file_info = ExperimentDataFileInfo(
            ref_genome=self.ref_genome,
            ref_genome_patch=self.ref_genome_patch,
            significance_measure=self.significance_measure,
            p_value_threshold=self.p_val_threshold,
        )
        data_file_info.save()
        self.file_metadata.db_save(experiment, analysis, data_file_info)


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
        cell_line = CellLine.objects.filter(name=self.cell_line).first()
        if cell_line is None:
            with AccessionIds(message=f"{self.experiment.accession_id}: {self.experiment.name}"[:200]) as accession_ids:
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
        bios = Biosample.objects.filter(
            cell_line=cell_line,
            cell_line_name=cell_line.name,
        ).first()
        if bios is None:
            bios = Biosample(
                cell_line=cell_line,
                cell_line_name=cell_line.name,
                accession_id=accession_ids.incr(AccessionType.BIOS),
            )
            bios.save()


class AnalysisMetadata:
    accession_id: Optional[str] = None
    experiment_accession_id: str
    filename: str
    description: str
    name: str
    results: list[ExperimentFileMetadata] = []

    def __init__(self, analysis_dict: dict[str, Any], analysis_filename: str):
        self.description = analysis_dict["description"]
        self.experiment_accession_id = analysis_dict["experiment"]
        self.filename = analysis_filename
        self.name = analysis_dict["name"]

        for result in analysis_dict["results"]:
            self.results.append(ExperimentFileMetadata(result))

    def db_save(self):
        experiment = Experiment.objects.get(accession_id=self.experiment_accession_id)
        with AccessionIds(message=f"Analysis of {experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
            analysis = Analysis(description=self.description, experiment=experiment, name=self.name)
            analysis.accession_id = accession_ids.incr(AccessionType.ANALYSIS)
            analysis.save()
            self.accession_id = analysis.accession_id
        for result in self.results:
            result.db_save(experiment, analysis)

        return analysis

    def db_del(self, analysis=None):
        if self.accession_id is None and analysis is None:
            print("Analysis has not been saved: There is no accession ID")
            return

        if self.accession_id is not None:
            analysis = Analysis.objects.get(accession_id=self.accession_id)

        for file in analysis.files.all():
            file.data_file_info.delete()
        analysis.delete()
        self.accession_id = None

    def metadata(self):
        base_path = os.path.dirname(self.filename)
        for result in self.results:
            delimiter = get_delimiter(result.file_metadata.filename)
            data_file = open(os.path.join(base_path, result.file_metadata.filename), "r", newline="")
            yield data_file, result, delimiter
            data_file.close()

    @classmethod
    def json_load(cls, file: IO):
        analysis_data = json.load(file)
        metadata = AnalysisMetadata(analysis_data, file.name)
        return metadata


class ExperimentMetadata:
    description: str
    experiment_type: str
    name: str
    filename: str
    accession_id: str
    biosamples: list[ExperimentBiosample]
    file_metadata: list[FileMetadata]

    def __init__(self, experiment_dict: dict[str, Any], experiment_filename: str):
        self.description = experiment_dict.get("description", None)
        self.experiment_type = experiment_dict.get("type", None)
        self.name = experiment_dict["name"]
        self.accession_id = experiment_dict["accession_id"]
        self.filename = experiment_filename
        self.file_metadata = []
        self.file_metadata = []
        self.biosamples = [ExperimentBiosample(sample, self) for sample in experiment_dict["biosamples"]]
        for file in experiment_dict.get("files", []):
            self.file_metadata.append(FileMetadata(file))

    def db_save(self):
        experiment = Experiment(
            name=self.name,
            accession_id=self.accession_id,
            description=self.description,
            experiment_type=self.experiment_type,
        )
        experiment.save()
        for file in self.file_metadata:
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
            if file.data_file_info is not None:
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
