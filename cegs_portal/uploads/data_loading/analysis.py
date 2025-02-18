import csv
import logging
import math
from dataclasses import dataclass
from io import StringIO
from itertools import tee
from typing import Optional

from django.db import transaction
from psycopg.types.range import Int4Range

from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    DNAFeature,
    DNAFeatureType,
    Experiment,
    Facet,
    FacetValue,
    RegulatoryEffectObservation,
)
from utils.db_ids import ReoIds

from .db import bulk_reo_save, cat_facet_entry, reo_entry, source_entry, target_entry
from .metadata import AnalysisMetadata, InternetFile
from .types import Facets, FeatureType

MIN_SIG = 1e-100

logger = logging.getLogger(__name__)


@dataclass
class FeatureInfo:
    name: Optional[str]
    chrom_name: str
    start: int
    end: int


@dataclass
class SourceInfo:
    chrom: str
    start: int
    end: int
    strand: Optional[str]
    feature_type: FeatureType

    def __post_init__(self):
        DNAFeatureType(self.feature_type)

        if self.strand == ".":
            self.strand = None

    def __str__(self):
        return f"{self.chrom}:{self.start}-{self.end}:{self.strand} {self.feature_type}"


@dataclass
class ObservationRow:
    name: Optional[str]
    sources: list[SourceInfo]
    targets: list[str]  # ensembl ids
    categorical_facets: list[list[str]]
    numeric_facets: dict[Facets, float]


class Analysis:
    metadata: AnalysisMetadata
    observations: Optional[list[ObservationRow]] = None
    accession_id: Optional[str] = None

    def __init__(self, metadata: AnalysisMetadata):
        self.metadata = metadata

        dir_facet = Facet.objects.get(name="Direction")
        self.categorical_facet_values = {
            facet_value.value: facet_value for facet_value in FacetValue.objects.filter(facet_id=dir_facet.id).all()
        }
        self.data_source = None

    def add_file_data_source(self, results_file_location):
        def _ds():
            results_tsv = InternetFile(results_file_location).file
            reader = csv.DictReader(results_tsv, delimiter="\t", quoting=csv.QUOTE_NONE)
            for line in reader:
                yield line
            results_tsv.close()

        self.data_source = _ds

        return self

    def add_generator_data_source(self, generator):
        def _ds():
            [new_gen] = tee(generator, 1)
            for line in new_gen:
                yield line

        self.data_source = _ds
        return self

    def load(self):
        assert self.data_source is not None

        source_type = FeatureType(self.metadata.source_type)

        observations: list[ObservationRow] = []
        for line in self.data_source():
            chrom_name, start, end, strand = (
                line["chrom"],
                int(line["start"]),
                int(line["end"]),
                line["strand"],
            )
            sources = [SourceInfo(chrom_name, start, end, strand, source_type)]

            if (target := line["gene_ensembl_id"]) != "":
                targets = [target]
            else:
                targets = []

            raw_p_value = float(line["raw_p_val"])
            adjusted_p_value = float(line["adj_p_val"])
            try:
                effect_size = float(line["effect_size"])
            except ValueError:
                effect_size = None
            categorical_facets = [f.split("=") for f in line["facets"].split(";")] if line["facets"] != "" else []

            for _, facet_value in categorical_facets:
                if facet_value not in self.categorical_facet_values:
                    raise ValueError(f"Invalid categorical facet value: '{facet_value}'")

            num_facets = {
                Facets.EFFECT_SIZE: effect_size,
                Facets.SIGNIFICANCE: adjusted_p_value,
                Facets.RAW_P_VALUE: raw_p_value,
            }

            name = line.get("name")

            observations.append(ObservationRow(name, sources, targets, categorical_facets, num_facets))

        self.observations = observations
        return self

    def _save_reos(self, accession_ids):
        if self.observations is None:
            return

        analysis_accession_id = self.accession_id
        experiment_accession_id = self.metadata.experiment_accession_id
        experiment = (
            Experiment.objects.filter(accession_id=experiment_accession_id).prefetch_related("facet_values").first()
        )
        assert experiment is not None
        experiment_id = experiment.id
        genome_assembly = self.metadata.genome_assembly
        sources = StringIO()
        targets = StringIO()
        effects = StringIO()
        cat_facets = StringIO()
        source_cache = {}
        target_cache = {}

        fcm_facet_value = None
        for facet_value in experiment.facet_values.all():
            if facet_value.facet.name == Experiment.Facet.FUNCTIONAL_CHARACTERIZATION.value:
                fcm_facet_value = facet_value

        with ReoIds() as reo_ids:
            for reo_id, reo in zip(reo_ids, self.observations):
                reo_direction = [fv for f, fv in reo.categorical_facets if f == "Direction"]

                for source in reo.sources:
                    source_string = f"{source.chrom}:{source.start}-{source.end}:{source.strand}:{genome_assembly}"
                    if source_string not in source_cache:
                        try:
                            source_cache[source_string] = DNAFeature.objects.filter(
                                experiment_accession_id=experiment_accession_id,
                                chrom_name=source.chrom,
                                location=Int4Range(source.start, source.end),
                                strand=source.strand,
                                ref_genome=genome_assembly,
                                feature_type=DNAFeatureType(source.feature_type),
                            ).values_list("id", flat=True)[0]
                        except Exception:
                            logger.debug(
                                f"{experiment_accession_id} {source.chrom}:{Int4Range(source.start, source.end)}:{source.strand} {genome_assembly} {source.feature_type}"
                            )
                            raise

                    feature_id = source_cache[source_string]
                    sources.write(source_entry(reo_id, feature_id))

                    feature = DNAFeature.objects.get(id=feature_id)
                    if fcm_facet_value is not None:
                        feature.facet_values.add(fcm_facet_value)

                    if reo_direction:
                        feature.significant_reo = feature.significant_reo or (reo_direction[0] != "Non-significant")
                        feature.facet_values.add(self.categorical_facet_values[reo_direction[0]])
                    feature.save()

                for target in reo.targets:
                    if target not in target_cache:
                        try:
                            target_cache[target] = DNAFeature.objects.filter(
                                ref_genome=genome_assembly, ensembl_id=target
                            ).values_list("id", flat=True)[0]
                        except Exception:
                            logger.debug(f"{genome_assembly} {target}")
                            raise

                    targets.write(target_entry(reo_id, target_cache[target]))

                facet_num_values = {
                    RegulatoryEffectObservation.Facet(key).value: value for key, value in reo.numeric_facets.items()
                }

                if Facets.LOG_SIGNIFICANCE not in facet_num_values:
                    facet_num_values[RegulatoryEffectObservation.Facet.LOG_SIGNIFICANCE.value] = -math.log10(
                        max(reo.numeric_facets[Facets.SIGNIFICANCE], MIN_SIG)
                    )

                effects.write(
                    reo_entry(
                        id_=reo_id,
                        name=reo.name,
                        accession_id=accession_ids.incr(AccessionType.REGULATORY_EFFECT_OBS),
                        experiment_id=experiment_id,
                        experiment_accession_id=experiment_accession_id,
                        analysis_accession_id=analysis_accession_id,
                        facet_num_values=facet_num_values,
                    )
                )

                for _, facet_value in reo.categorical_facets:
                    facet_value_id = self.categorical_facet_values[facet_value].id
                    cat_facets.write(cat_facet_entry(reo_id, facet_value_id))

                # Write the experiment's Functional Characterization Modality as a facet on the REO
                if fcm_facet_value is not None:
                    cat_facets.write(cat_facet_entry(reo_id, fcm_facet_value.id))

        bulk_reo_save(effects, cat_facets, sources, targets)

    def save(self):
        with transaction.atomic():
            analysis = self.metadata.db_save()
            self.accession_id = analysis.accession_id

            with AccessionIds(message=f"{self.accession_id}: {self.metadata.name}"[:200]) as accession_ids:
                self._save_reos(accession_ids)

        return self


def load(analysis_filename, experiment_accession_id):
    metadata = AnalysisMetadata.load(analysis_filename, experiment_accession_id)
    analysis = Analysis(metadata).add_file_data_source(metadata.results.file_location).load().save()
    return analysis.accession_id
