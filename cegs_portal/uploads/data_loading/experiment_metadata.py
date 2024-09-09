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
        case "chromatin accessible region":
            return DNAFeatureSourceType.CAR
        case "grna":
            return DNAFeatureSourceType.GRNA
        case "dhs":
            return DNAFeatureSourceType.DHS
        case "ccre":
            return DNAFeatureSourceType.CCRE
        case "called regulatory element":
            return DNAFeatureSourceType.CRE
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

    def _file_load(self, file_path: str):
        return open(file_path, "r")

    def _http_load(self, file_url: str):
        with requests.get(file_url) as response:
            if not response.ok:
                raise ValueError(f"Unable to download {file_url}: {response.status_code} {response.reason}")

            return StringIO(response.text)

    def _s3_load(self, file_url: str):
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
    results: FileMetadata
    genome_assembly: str
    genome_assembly_patch: str
    p_val_threshold: float
    p_val_adj_method: str
    data_format: str
    misc_files: list[FileMetadata]

    def __init__(self, analysis_dict: dict[str, Any], experiment_accession_id):
        self.description = analysis_dict["description"]
        self.experiment_accession_id = experiment_accession_id
        self.name = analysis_dict["name"]
        assert self.name != ""

        self.results = FileMetadata(analysis_dict["results"])
        self.genome_assembly = analysis_dict["genome_assembly"]
        self.genome_assembly_patch = analysis_dict.get("genome_assembly_patch", None)
        self.p_val_threshold = analysis_dict["p_val_threshold"]
        self.p_val_adj_method = analysis_dict.get("p_val_adj_method", "unknown")

        self.source_type = analysis_dict["source type"]
        self.data_format = analysis_dict.get("data_format", "standard")
        self.misc_files = (
            [FileMetadata(file) for file in analysis_dict["misc_files"]] if "misc_files" in analysis_dict else []
        )

    def db_save(self):
        experiment = Experiment.objects.get(accession_id=self.experiment_accession_id)
        with AccessionIds(message=f"Analysis of {experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
            analysis = Analysis(
                description=self.description,
                experiment=experiment,
                name=self.name,
                genome_assembly=self.genome_assembly,
                genome_assembly_patch=self.genome_assembly_patch,
                p_value_threshold=self.p_val_threshold,
                p_value_adj_method=self.p_val_adj_method,
            )
            analysis.accession_id = accession_ids.incr(AccessionType.ANALYSIS)
            analysis.save()
            self.accession_id = analysis.accession_id

            # Set the new analysis as default
            experiment.default_analysis = analysis
            experiment.save()

            self.results.db_save(experiment, analysis)

        return analysis

    def db_del(self, analysis=None):
        if self.accession_id is None and analysis is None:
            print("Analysis has not been saved: There is no accession ID")
            return

        if self.accession_id is not None:
            analysis = Analysis.objects.get(accession_id=self.accession_id)

        analysis.delete()
        self.accession_id = None


class ExperimentMetadata(Metadata):
    description: Optional[str]
    assay: Optional[str]
    name: str
    crispr: Optional[str]
    accession_id: str
    biosamples: list[ExperimentBiosample]
    source_type: str
    data_format: str
    parent_source_type: Optional[str]
    tested_elements_file: FileMetadata
    misc_files: list[FileMetadata]

    def __init__(self, experiment_dict: dict[str, Any], accession_id):
        self.description = experiment_dict.get("description")
        self.assay = experiment_dict.get("assay")
        self.name = experiment_dict["name"]
        assert self.name != ""
        self.crispr = experiment_dict.get("crispr")
        self.accession_id = accession_id
        self.source_type = experiment_dict["source type"]
        self.data_format = experiment_dict.get("data_format", "standard")
        self.parent_source_type = (
            experiment_dict["parent source type"] if "parent source type" in experiment_dict else None
        )

        self.biosamples = [ExperimentBiosample(sample) for sample in experiment_dict["biosamples"]]
        self.tested_elements_file = FileMetadata(experiment_dict["tested_elements_file"], self.biosamples)
        self.misc_files = (
            [FileMetadata(file) for file in experiment_dict["misc_files"]] if "misc_files" in experiment_dict else []
        )

    def db_save(self):
        experiment = Experiment(
            name=self.name,
            accession_id=self.accession_id,
            description=self.description,
            experiment_type=self.assay,
            source_type=get_source_type(self.source_type),
        )
        experiment.save()

        if self.assay is not None:
            assay_facet = FacetValue.objects.get(value=self.assay)
            experiment.facet_values.add(assay_facet)

        source_facet = FacetValue.objects.get(value__iexact=self.source_type)
        experiment.facet_values.add(source_facet)

        if self.crispr is not None:
            crispr_facet = FacetValue.objects.get(value=self.crispr)
            experiment.facet_values.add(crispr_facet)

        assembly_facet = FacetValue.objects.get(value__iexact=self.tested_elements_file.genome_assembly)
        experiment.facet_values.add(assembly_facet)

        experiment.save()

        self.tested_elements_file.db_save(experiment)

        accession_log = AccessionIdLog(
            created_at=datetime.now(timezone.utc),
            accession_type=AccessionType.EXPERIMENT,
            accession_id=self.accession_id,
            message=self.description[:200] if self.description is not None else "",
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
            file.delete()

        experiment.delete()
