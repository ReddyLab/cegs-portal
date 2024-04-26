import json
from datetime import datetime, timezone
from io import StringIO
from typing import Any, Optional

import requests
from django.core.files.uploadedfile import UploadedFile

from cegs_portal.search.models import (
    AccessionIdLog,
    AccessionIds,
    AccessionType,
    Analysis,
    DNAFeatureSourceType,
    Experiment,
    FacetValue,
)

from .biosample import ExperimentBiosample
from .file import FileMetadata

MAX_METADATA_CONTENT_LENGTH = 65_536


def get_source_type(source_type_string) -> DNAFeatureSourceType:
    match source_type_string.lower():
        case "car":
            return DNAFeatureSourceType.CAR
        case "grna":
            return DNAFeatureSourceType.GRNA
        case "dhs":
            return DNAFeatureSourceType.DHS
        case "ccre":
            return DNAFeatureSourceType.CCRE
        case _:
            raise Exception(f"Bad source feature string: {source_type_string}")


class InternetFile:
    def __init__(self, file: str | UploadedFile):
        if isinstance(file, str):
            if file.startswith("http://") or file.startswith("https://"):
                self.file = self._http_load(file)
            elif file.startswith("s3://"):
                self.file = self._s3_load(file)
            else:
                self.file = self._file_load(file)
        else:
            self.file = file

    def _file_load(cls, file_path: str):
        return open(file_path, "r")

    def _http_load(cls, file_url: str):
        with requests.get(file_url) as response:
            if not response.ok:
                raise ValueError(f"Unable to download {file_url}: {response.status_code} {response.reason}")

            return StringIO(response.text)

    def _s3_load(cls, file_url: str):
        return open(file_url, "r")

    def close(self):
        self.file.close()


class Metadata:
    @classmethod
    def load(cls, file: str | UploadedFile, experiment_accession_id: str):
        data = json.load(InternetFile(file).file)
        metadata = cls(data, experiment_accession_id)
        return metadata


class AnalysisMetadata(Metadata):
    accession_id: Optional[str] = None
    experiment_accession_id: str
    description: str
    name: str
    source_type: str
    file_metadata: FileMetadata
    genome_assembly: str
    genome_assembly_patch: str
    p_val_threshold: float
    p_val_adj_method: str

    def __init__(self, analysis_dict: dict[str, Any], experiment_accession_id, file_metadata: dict[str, str]):
        self.description = analysis_dict["description"]
        self.experiment_accession_id = experiment_accession_id
        self.name = analysis_dict["name"]
        assert self.name != ""

        self.file_metadata = FileMetadata(file_metadata)
        self.genome_assembly = file_metadata["genome_assembly"]
        self.genome_assembly_patch = file_metadata.get("genome_assembly_patch", None)
        self.p_val_threshold = file_metadata["p_val_threshold"]
        self.p_val_adj_method = file_metadata.get("p_val_adj_method", "unknown")

        self.source_type = get_source_type(analysis_dict["source type"])

    def db_save(self):
        experiment = Experiment.objects.get(accession_id=self.experiment_accession_id)
        with AccessionIds(message=f"Analysis of {experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
            analysis = Analysis(
                description=self.description,
                experiment=experiment,
                name=self.name,
                ref_genome=self.genome_assembly,
                ref_genome_patch=self.genome_assembly_patch,
                p_value_threshold=self.p_val_threshold,
                p_value_adj_method=self.p_val_adj_method,
            )
            analysis.accession_id = accession_ids.incr(AccessionType.ANALYSIS)
            analysis.save()
            self.accession_id = analysis.accession_id

            # Set the new analysis as default
            experiment.default_analysis = analysis
            experiment.save()

            self.file_metadata.db_save(experiment, analysis)

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


class ExperimentMetadata(Metadata):
    description: str
    assay: str
    name: str
    accession_id: str
    biosamples: list[ExperimentBiosample]
    source_type: str
    parent_source_type: Optional[str]
    tested_elements_file: FileMetadata

    def __init__(self, experiment_dict: dict[str, Any], accession_id):
        self.description = experiment_dict.get("description", None)
        self.assay = experiment_dict.get("assay", None)
        self.name = experiment_dict["name"]
        assert self.name != ""
        self.accession_id = accession_id
        self.source_type = get_source_type(experiment_dict["source type"])
        self.parent_source_type = (
            get_source_type(experiment_dict["parent source type"]) if "parent source type" in experiment_dict else None
        )
        self.biosamples = [ExperimentBiosample(sample) for sample in experiment_dict["biosamples"]]
        self.tested_elements_file = FileMetadata(experiment_dict["tested_elements_file"], self.biosamples)

    def db_save(self):
        experiment = Experiment(
            name=self.name,
            accession_id=self.accession_id,
            description=self.description,
            experiment_type=self.assay,
            source_type=self.source_type,
        )
        experiment.save()
        assay_facet = FacetValue.objects.get(value=self.assay)
        source_facet = FacetValue.objects.get(value__iexact=self.source_type)
        experiment.facet_values.add(assay_facet)
        experiment.facet_values.add(source_facet)
        experiment.save()

        self.tested_elements_file.db_save(experiment)

        accession_log = AccessionIdLog(
            created_at=datetime.now(timezone.utc),
            accession_type=AccessionType.EXPERIMENT,
            accession_id=self.accession_id,
            message=self.description[:200],
        )
        accession_log.save()
        for biosample in self.biosamples:
            bios = biosample.db_save(self)
            experiment.biosamples.add(bios)
            cell_line_facet = FacetValue.objects.get(value__iexact=biosample.cell_line)
            tissue_type_facet = FacetValue.objects.get(value__iexact=biosample.tissue_type)
            experiment.facet_values.add(cell_line_facet)
            experiment.facet_values.add(tissue_type_facet)
        return experiment

    def db_del(self):
        experiment = Experiment.objects.get(accession_id=self.accession_id)
        for file in experiment.files.all():
            if file.data_file_info is not None:
                for data in file.data_file_info.all():
                    data.delete()
            file.delete()

        experiment.delete()
