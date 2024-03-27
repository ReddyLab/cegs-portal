import json
import os.path
from datetime import datetime, timezone
from typing import Any, Optional

import requests

from cegs_portal.search.models import (
    AccessionIdLog,
    AccessionIds,
    AccessionType,
    Analysis,
    DNAFeatureSourceType,
    Experiment,
    ExperimentDataFileInfo,
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


class ExperimentFileMetadata:
    file_metadata: FileMetadata
    genome_assembly: str
    genome_assembly_patch: str
    p_val_threshold: float

    def __init__(self, file_metadata: dict[str, str], base_path: Optional[str] = None):
        self.file_metadata = FileMetadata(file_metadata, base_path)
        self.genome_assembly = file_metadata["genome_assembly"]
        self.genome_assembly_patch = file_metadata.get("genome_assembly_patch", None)
        self.p_val_threshold = file_metadata.get("p_val_threshold", 0.05)

    def db_save(self, experiment: Experiment, analysis: Analysis = None):
        data_file_info = ExperimentDataFileInfo(
            ref_genome=self.genome_assembly,
            ref_genome_patch=self.genome_assembly_patch,
            p_value_threshold=self.p_val_threshold,
        )
        data_file_info.save()
        self.file_metadata.db_save(experiment, analysis, data_file_info)


class Metadata:
    @classmethod
    def load(cls, file_url: str, experiment_accession_id: str):
        if file_url.startswith("http://") or file_url.startswith("https://"):
            return cls.http_load(file_url, experiment_accession_id)
        elif file_url.startswith("s3://"):
            return cls.s3_load(file_url, experiment_accession_id)
        else:
            return cls.file_load(file_url, experiment_accession_id)

    @classmethod
    def file_load(cls, file_path: str, experiment_accession_id: str):
        with open(file_path) as file:
            experiment_data = json.load(file)
            metadata = cls(experiment_data, experiment_accession_id, file.name)
        return metadata

    @classmethod
    def http_load(cls, file_url: str, experiment_accession_id: str):
        with requests.get(file_url, stream=True) as response:
            if (content_length := int(response.headers["content-length"])) > MAX_METADATA_CONTENT_LENGTH:
                raise ValueError(
                    f"Content Metadata {file_url} too long. Size: {content_length}, Max Size: {MAX_METADATA_CONTENT_LENGTH}"
                )

            data = response.json
            metadata = cls(data, experiment_accession_id)
        return metadata

    @classmethod
    def s3_load(cls, file_url: str, experiment_accession_id: str):
        with open(file_url) as file:
            data = json.load(file)
            metadata = cls(data, experiment_accession_id)
        return metadata


class AnalysisMetadata(Metadata):
    accession_id: Optional[str] = None
    experiment_accession_id: str
    filename: str
    description: str
    name: str
    source_type: str
    results: ExperimentFileMetadata
    misc_files: list[FileMetadata] = []

    def __init__(self, analysis_dict: dict[str, Any], experiment_accession_id, analysis_filename: Optional[str] = None):
        self.description = analysis_dict["description"]
        self.experiment_accession_id = experiment_accession_id
        self.filename = analysis_filename
        self.name = analysis_dict["name"]
        assert self.name != ""

        self.source_type = get_source_type(analysis_dict["source type"])

        base_path = os.path.dirname(analysis_filename) if analysis_filename is not None else None

        self.results = ExperimentFileMetadata(analysis_dict["results"], base_path)

        self.misc_files = [FileMetadata(file, base_path) for file in analysis_dict.get("misc_files", [])]

    def db_save(self):
        experiment = Experiment.objects.get(accession_id=self.experiment_accession_id)
        with AccessionIds(message=f"Analysis of {experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
            analysis = Analysis(description=self.description, experiment=experiment, name=self.name)
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

        for file in analysis.files.all():
            file.data_file_info.delete()
        analysis.delete()
        self.accession_id = None


class ExperimentMetadata(Metadata):
    description: str
    assay: str
    name: str
    filename: str
    accession_id: str
    biosamples: list[ExperimentBiosample]
    file_metadata: list[FileMetadata]
    source_type: str
    tested_elements_file: FileMetadata
    tested_elements_parent_file: Optional[FileMetadata]

    def __init__(self, experiment_dict: dict[str, Any], accession_id, experiment_filename: Optional[str] = None):
        self.description = experiment_dict.get("description", None)
        self.assay = experiment_dict.get("assay", None)
        self.name = experiment_dict["name"]
        assert self.name != ""
        self.accession_id = accession_id
        self.source_type = get_source_type(experiment_dict["source type"])
        self.filename = experiment_filename
        base_path = os.path.dirname(experiment_filename) if experiment_filename is not None else None
        self.biosamples = [ExperimentBiosample(sample) for sample in experiment_dict["biosamples"]]
        self.file_metadata = [FileMetadata(file, base_path, self.biosamples) for file in experiment_dict["files"]]

        self.tested_elements_file = self.file_metadata[int(experiment_dict["tested_elements_file"])]

        if (tested_elements_parent_file_idx := experiment_dict.get("tested_elements_parent_file")) is not None:
            self.tested_elements_parent_file = self.file_metadata[int(tested_elements_parent_file_idx)]

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
