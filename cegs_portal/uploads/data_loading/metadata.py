import json
import logging
from datetime import datetime, timezone
from enum import StrEnum
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
from .file import AnalysisResultsMetadata, TestedElementsMetadata

MAX_METADATA_CONTENT_LENGTH = 65_536

logger = logging.getLogger(__name__)


class AnalysisMetadataKeys(StrEnum):
    NAME = "name"
    DESCRIPTION = "description"
    SOURCE_TYPE = "source type"
    GENOME_ASSEMBLY = "genome_assembly"
    P_VAL_THRESHOLD = "p_val_threshold"
    P_VAL_ADJ_METHOD = "p_val_adj_method"
    RESULTS = "results"


class ExperimentMetadataKeys(StrEnum):
    DESCRIPTION = "description"
    ASSAY = "assay"
    NAME = "name"
    BIOSAMPLES = "biosamples"
    SOURCE_TYPE = "source type"
    PARENT_SOURCE_TYPE = "parent source type"
    YEAR = "year"
    LAB = "lab"
    FUNCTIONAL_CHARACTERIZATION = "functional_characterization_modality"
    TESTED_ELEMENTS_METADATA = "tested_elements_file"
    PROVENANCE = "provenance"


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
        case "genomic element":
            return DNAFeatureSourceType.GE
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
    experiment_accession_id: str
    description: str
    name: str
    source_type: str
    results: AnalysisResultsMetadata
    genome_assembly: str
    p_val_threshold: float
    p_val_adj_method: str
    data_format: str
    accession_id: Optional[str] = None
    analysis: Optional[Analysis] = None

    def __init__(self, analysis_dict: dict[str, Any], experiment_accession_id: str):
        self.description = analysis_dict[AnalysisMetadataKeys.DESCRIPTION]
        self.experiment_accession_id = experiment_accession_id
        self.name = analysis_dict[AnalysisMetadataKeys.NAME]
        assert self.name != ""

        self.results = AnalysisResultsMetadata(analysis_dict[AnalysisMetadataKeys.RESULTS])
        self.genome_assembly = analysis_dict[AnalysisMetadataKeys.GENOME_ASSEMBLY]
        self.p_val_threshold = analysis_dict[AnalysisMetadataKeys.P_VAL_THRESHOLD]
        self.p_val_adj_method = analysis_dict.get(AnalysisMetadataKeys.P_VAL_ADJ_METHOD, "unknown")

        self.source_type = analysis_dict[AnalysisMetadataKeys.SOURCE_TYPE]

    def db_save(self):
        experiment = Experiment.objects.get(accession_id=self.experiment_accession_id)
        with AccessionIds(message=f"Analysis of {experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
            analysis = Analysis(
                description=self.description,
                experiment=experiment,
                name=self.name,
                genome_assembly=self.genome_assembly,
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

        self.analysis = analysis
        return analysis

    def db_del(self, analysis=None):
        if self.accession_id is None and analysis is None:
            logger.warning("Analysis has not been saved: There is no accession ID")
            return

        if self.accession_id is not None:
            analysis = Analysis.objects.get(accession_id=self.accession_id)

        analysis.delete()
        self.accession_id = None


class ExperimentMetadata(Metadata):
    description: Optional[str]
    assay: Optional[str]
    name: str
    functional_characterization: Optional[str]
    accession_id: str
    biosamples: list[ExperimentBiosample]
    source_type: str
    parent_source_type: Optional[str]
    provenance: Optional[str]
    tested_elements_metadata: TestedElementsMetadata
    experiment: Optional[Experiment] = None

    def __init__(self, experiment_dict: dict[str, Any], accession_id: str):
        self.description = experiment_dict.get(ExperimentMetadataKeys.DESCRIPTION)
        self.assay = experiment_dict.get(ExperimentMetadataKeys.ASSAY)
        self.name = experiment_dict[ExperimentMetadataKeys.NAME]
        assert self.name != ""
        self.functional_characterization = experiment_dict.get(ExperimentMetadataKeys.FUNCTIONAL_CHARACTERIZATION)
        self.accession_id = accession_id
        self.source_type = experiment_dict[ExperimentMetadataKeys.SOURCE_TYPE]
        self.parent_source_type = experiment_dict.get(ExperimentMetadataKeys.PARENT_SOURCE_TYPE)

        self.biosamples = [ExperimentBiosample(sample) for sample in experiment_dict[ExperimentMetadataKeys.BIOSAMPLES]]
        self.provenance = experiment_dict.get(ExperimentMetadataKeys.PROVENANCE)
        tested_elements_metadata = experiment_dict.get(ExperimentMetadataKeys.TESTED_ELEMENTS_METADATA)
        if tested_elements_metadata is not None:
            self.tested_elements_metadata = TestedElementsMetadata(tested_elements_metadata)

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

        if self.functional_characterization is not None:
            fc_facet = FacetValue.objects.get(value=self.functional_characterization)
            experiment.facet_values.add(fc_facet)

        if self.provenance is not None:
            p_facet = FacetValue.objects.get(value=self.provenance)
            experiment.facet_values.add(p_facet)

        assembly_facet = FacetValue.objects.get(value__iexact=self.tested_elements_metadata.genome_assembly)
        experiment.facet_values.add(assembly_facet)

        experiment.save()

        self.tested_elements_metadata.db_save(experiment)

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

        self.experiment = experiment
        return experiment

    def db_del(self):
        experiment = Experiment.objects.get(accession_id=self.accession_id)
        for file in experiment.files.all():
            file.delete()

        experiment.delete()
