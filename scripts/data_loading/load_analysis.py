import math
from dataclasses import dataclass
from io import StringIO
from typing import Optional

from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import AccessionIds, AccessionType
from cegs_portal.search.models import Analysis as AnalysisModel
from cegs_portal.search.models import (
    DNAFeature,
    DNAFeatureType,
    Experiment,
    Facet,
    FacetValue,
    RegulatoryEffectObservation,
)
from utils.db_ids import ReoIds
from utils.experiment import AnalysisMetadata

from .db import bulk_reo_save, cat_facet_entry, reo_entry, source_entry, target_entry
from .types import FeatureType, NumericFacets

DIR_FACET = Facet.objects.get(name="Direction")
DIR_FACET_VALUES = {facet.value: facet.id for facet in FacetValue.objects.filter(facet_id=DIR_FACET.id).all()}

CATEGORICAL_FACET_VALUES = DIR_FACET_VALUES

MIN_SIG = 1e-100


@dataclass
class FeatureInfo:
    name: Optional[str]
    chrom_name: str
    start: int
    end: int
    bounds: str


@dataclass
class SourceInfo:
    chrom: str
    start: int
    end: int
    bounds: str
    strand: Optional[str]
    feature_type: FeatureType

    def __post_init__(self):
        DNAFeatureType(self.feature_type)


@dataclass
class ObservationRow:
    sources: list[SourceInfo]
    targets: list[str]  # ensembl ids
    categorical_facets: list[str]
    numeric_facets: dict[str:float]

    def __post_init__(self):
        for facet in self.categorical_facets:
            if facet not in CATEGORICAL_FACET_VALUES:
                raise ValueError(f"Invalid categorical facet: '{facet}'")


class Analysis:
    observations: Optional[list[ObservationRow]] = None
    accession_id: Optional[str] = None

    def __init__(self, metadata: AnalysisMetadata):
        self.metadata = metadata

    def load(self, load_function):
        self.observations = load_function(self.metadata)

        return self

    def _save_reos(self, reos: list[ObservationRow], accession_ids):
        analysis_accession_id = self.accession_id
        experiment_accession_id = self.metadata.experiment_accession_id
        experiment_id = Experiment.objects.filter(accession_id=experiment_accession_id).values_list("id", flat=True)[0]
        genome_assembly = self.metadata.results.genome_assembly
        sources = StringIO()
        targets = StringIO()
        effects = StringIO()
        cat_facets = StringIO()
        source_cache = {}
        target_cache = {}

        with ReoIds() as reo_ids:
            for reo_id, reo in zip(reo_ids, reos):
                for source in reo.sources:
                    source_string = f"{source.chrom}:{source.start}-{source.end}:{source.strand}:{genome_assembly}"

                    if source_string not in source_cache:
                        source_cache[source_string] = DNAFeature.objects.filter(
                            experiment_accession_id=experiment_accession_id,
                            chrom_name=source.chrom,
                            location=NumericRange(source.start, source.end, source.bounds),
                            strand=source.strand,
                            ref_genome=genome_assembly,
                            feature_type=DNAFeatureType(source.feature_type),
                        ).values_list("id", flat=True)[0]

                    sources.write(source_entry(reo_id, source_cache[source_string]))

                for target in reo.targets:
                    if target not in target_cache:
                        target_cache[target] = DNAFeature.objects.filter(
                            ref_genome=genome_assembly, ensembl_id=target
                        ).values_list("id", flat=True)[0]

                    targets.write(target_entry(reo_id, target_cache[target]))

                facet_num_values = {
                    RegulatoryEffectObservation.Facet(key).value: value for key, value in reo.numeric_facets.items()
                }

                if NumericFacets.LOG_SIGNIFICANCE not in facet_num_values:
                    facet_num_values[RegulatoryEffectObservation.Facet.LOG_SIGNIFICANCE.value] = -math.log10(
                        max(reo.numeric_facets[NumericFacets.SIGNIFICANCE], MIN_SIG)
                    )
                effects.write(
                    reo_entry(
                        id_=reo_id,
                        accession_id=accession_ids.incr(AccessionType.REGULATORY_EFFECT_OBS),
                        experiment_id=experiment_id,
                        experiment_accession_id=experiment_accession_id,
                        analysis_accession_id=analysis_accession_id,
                        facet_num_values=facet_num_values,
                    )
                )

                for facet in reo.categorical_facets:
                    if facet is None:
                        continue

                    facet_id = CATEGORICAL_FACET_VALUES[facet]
                    cat_facets.write(cat_facet_entry(reo_id, facet_id))

        bulk_reo_save(effects, cat_facets, sources, targets)

    def save(self):
        with transaction.atomic():
            analysis = self.metadata.db_save()
            self.accession_id = analysis.accession_id

            with AccessionIds(message=f"{self.accession_id}: {self.metadata.name}"[:200]) as accession_ids:
                self._save_reos(self.observations, accession_ids)

        return self

    def delete(self):
        analysis = AnalysisModel.objects.get(
            experiment_accession_id=self.metadata.experiment_accession_id, name=self.metadata.name
        )
        RegulatoryEffectObservation.objects.filter(analysis=analysis).delete()
        self.metadata.db_del(analysis)
