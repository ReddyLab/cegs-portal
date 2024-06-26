import json
import os.path
from datetime import datetime, timezone
from typing import Any, Optional

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
from .misc import get_delimiter


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


class AnalysisMetadata:
    accession_id: Optional[str] = None
    experiment_accession_id: str
    filename: str
    description: str
    name: str
    source_type: str
    results: FileMetadata
    genome_assembly: str
    genome_assembly_patch: str
    p_val_threshold: float
    p_val_adj_method: str

    def __init__(self, analysis_dict: dict[str, Any], analysis_filename: str):
        self.description = analysis_dict["description"]
        self.experiment_accession_id = analysis_dict["experiment"]
        self.filename = analysis_filename
        self.name = analysis_dict["name"]
        assert self.name != ""

        self.results = FileMetadata(analysis_dict["results"])
        self.genome_assembly = analysis_dict["genome_assembly"]
        self.genome_assembly_patch = analysis_dict.get("genome_assembly_patch", None)
        self.p_val_threshold = analysis_dict["p_val_threshold"]
        self.p_val_adj_method = analysis_dict.get("p_val_adj_method", "unknown")

        self.source_type = get_source_type(analysis_dict["source type"])

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

    def metadata(self):
        base_path = os.path.dirname(self.filename)
        for result in self.results:
            delimiter = get_delimiter(result.filename)
            data_file = open(os.path.join(base_path, result.filename), "r", newline="")
            yield data_file, result, delimiter
            data_file.close()

    @classmethod
    def file_load(cls, filename):
        with open(filename) as file:
            analysis_data = json.load(file)
            metadata = AnalysisMetadata(analysis_data, file.name)
        return metadata


class ExperimentMetadata:
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

    def __init__(self, experiment_dict: dict[str, Any], experiment_filename: str):
        self.description = experiment_dict.get("description", None)
        self.assay = experiment_dict.get("assay", None)
        self.name = experiment_dict["name"]
        assert self.name != ""
        self.accession_id = experiment_dict["accession_id"]
        self.source_type = get_source_type(experiment_dict["source type"])
        self.filename = experiment_filename
        base_path = os.path.dirname(experiment_filename)
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
            file.delete()

        experiment.delete()

    @classmethod
    def file_load(cls, filename: str):
        with open(filename) as file:
            experiment_data = json.load(file)
            metadata = ExperimentMetadata(experiment_data, file.name)
        return metadata
