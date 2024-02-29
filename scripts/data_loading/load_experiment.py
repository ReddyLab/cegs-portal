from dataclasses import dataclass
from io import StringIO
from typing import Any, Optional

from django.db import transaction
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    DNAFeature,
    DNAFeatureType,
)
from cegs_portal.search.models import Experiment as ExperimentModel
from cegs_portal.search.models import Facet, FacetValue
from utils.db_ids import FeatureIds
from utils.experiment import ExperimentMetadata

from . import get_closest_gene
from .db import (
    bulk_feature_facet_save,
    bulk_feature_save,
    feature_entry,
    feature_facet_entry,
)

GRNA_TYPE_FACET = Facet.objects.get(name="gRNA Type")
GRNA_TYPE_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=GRNA_TYPE_FACET.id).all()}
GRNA_TYPE_POS_CTRL = GRNA_TYPE_FACET_VALUES["Positive Control"]
GRNA_TYPE_TARGETING = GRNA_TYPE_FACET_VALUES["Targeting"]

PROMOTER_FACET = Facet.objects.get(name="Promoter Classification")
PROMOTER_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=PROMOTER_FACET.id).all()}
PROMOTER_PROMOTER = PROMOTER_FACET_VALUES["Promoter"]
PROMOTER_NON_PROMOTER = PROMOTER_FACET_VALUES["Non-promoter"]

FACET_VALUES = GRNA_TYPE_FACET_VALUES | PROMOTER_FACET_VALUES

VALID_BOUNDS = {"[]", "()", "[)", "(]"}
VALID_GENOME_ASSEMBLY = {"GRCh38", "GRCh37"}
VALID_FEATURE_TYPES = {v.value for v in DNAFeatureType}
VALID_STRANDS = {"+", "-"}
VALID_FACETS = {facet_value for facet_value in FACET_VALUES}


@dataclass
class FeatureRow:
    name: Optional[str]
    chrom_name: str
    location: tuple[int, int, str]  # start, end, bounds ("[]", "()", "[)", "(]")
    genome_assembly: str  # ("GRCh38", "GRCh37")
    cell_line: str
    feature_type: str  # ("cCRE", "DHS", "gRNA", "Chromatin Accessible Region")
    facets: Optional[list[str]] = None  # list[("Positive Control", "Targeting", "Promoter", "Non-promoter")]
    parent_name: Optional[str] = None
    misc: Optional[Any] = None
    strand: Optional[str] = None  # Optional[("+", "-")]

    def __post_init__(self):
        if self.strand is not None and self.strand not in VALID_STRANDS:
            raise ValueError(f"Invalid strand: '{self.strand}'")

        _, _, bounds = self.location
        if bounds not in VALID_BOUNDS:
            raise ValueError(f"Invalid bounds for feature location: '{bounds}'")

        if self.genome_assembly not in VALID_GENOME_ASSEMBLY:
            raise ValueError(f"Invalid genome assembly: '{self.genome_assembly}'")

        if self.feature_type not in VALID_FEATURE_TYPES:
            raise ValueError(f"Invalid feature type: '{self.feature_type}'")

        if self.facets is not None and not all(facet in VALID_FACETS for facet in self.facets):
            raise ValueError(f"Invalid facets: '{self.facets}'")


class Experiment:
    def __init__(
        self,
        metadata: ExperimentMetadata,
        features: list[FeatureRow],
        parent_features: Optional[list[FeatureRow]] = None,
    ):
        self.metadata = metadata
        self.features = features
        self.parent_features = parent_features
        self.accession_id = None

    def _save_features(self, features, accession_ids, source_file_id, parents=None):
        experiment_accession_id = self.accession_id
        feature_rows = StringIO()
        feature_facets = StringIO()
        db_ids = {}
        with FeatureIds() as feature_ids:
            for feature, feature_id in zip(features, feature_ids):
                feature_location = NumericRange(*feature.location)
                closest_gene, distance, gene_name = get_closest_gene(
                    feature.genome_assembly, feature.chrom_name, feature_location.lower, feature_location.upper
                )
                closest_gene_ensembl_id = closest_gene["ensembl_id"] if closest_gene is not None else None
                accession_type = AccessionType.from_feature_type(feature.feature_type)
                accession_id = accession_ids.incr(accession_type)
                db_ids[feature.name] = (feature_id, accession_id)
                if parents is not None:
                    parent_id, parent_accession_id = parents[feature.parent_name]
                else:
                    parent_id, parent_accession_id = (None, None)

                feature_rows.write(
                    feature_entry(
                        id_=feature_id,
                        accession_id=accession_id,
                        cell_line=feature.cell_line,
                        chrom_name=feature.chrom_name,
                        location=feature_location,
                        closest_gene_id=closest_gene["id"],
                        closest_gene_distance=distance,
                        closest_gene_name=gene_name,
                        closest_gene_ensembl_id=closest_gene_ensembl_id,
                        genome_assembly=feature.genome_assembly,
                        feature_type=DNAFeatureType(feature.feature_type),
                        source_file_id=source_file_id,
                        parent_id=parent_id,
                        parent_accession_id=parent_accession_id,
                        experiment_accession_id=experiment_accession_id,
                    )
                )
                if feature.facets is not None:
                    for facet in feature.facets:
                        feature_facets.write(
                            feature_facet_entry(feature_id=feature_id, facet_id=FACET_VALUES[facet].id)
                        )

        bulk_feature_save(feature_rows)
        bulk_feature_facet_save(feature_facets)
        return db_ids

    def _save_ccres(self, accession_ids):
        pass

    def save(self):
        with transaction.atomic():
            experiment = self.metadata.db_save()
            self.accession_id = experiment.accession_id

            with AccessionIds(message=f"{experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
                parents = None
                if self.parent_features is not None:
                    parent_file = self.metadata.tested_elements_parent_file
                    parents = self._save_features(self.parent_features, accession_ids, parent_file.id_)

                feature_file = self.metadata.tested_elements_file
                self._save_features(self.features, accession_ids, feature_file.id_, parents)
                self._save_ccres(accession_ids)

    def delete(self):
        """Only run delete if you want to delete the experiment, all
        associated reg effects, and any DNAFeatures created from the DB.
        Please note that it won't reset DB id numbers, so running this script with
        delete() uncommented is not, strictly, idempotent."""

        experiment = ExperimentModel.objects.get(accession_id=self.metadata.accession_id)
        DNAFeature.objects.filter(experiment_accession=experiment).delete()
        self.metadata.db_del()
