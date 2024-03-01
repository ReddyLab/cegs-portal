from dataclasses import dataclass, field
from enum import Enum
from io import StringIO
from typing import Any, Optional

from django.db import transaction
from django.db.models import F, Func
from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    DNAFeature,
    DNAFeatureType,
)
from cegs_portal.search.models import Experiment as ExperimentModel
from cegs_portal.search.models import Facet, FacetValue, GrnaType, PromoterType
from utils.db_ids import FeatureIds
from utils.experiment import ExperimentMetadata

from . import get_closest_gene
from .db import (
    bulk_feature_facet_save,
    bulk_feature_save,
    bulk_save_associations,
    ccre_associate_entry,
    feature_entry,
    feature_facet_entry,
)

GRNA_TYPE_FACET = Facet.objects.get(name=DNAFeature.Facet.GRNA_TYPE.value)
GRNA_TYPE_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=GRNA_TYPE_FACET.id).all()}
GRNA_TYPE_POS_CTRL = GRNA_TYPE_FACET_VALUES[GrnaType.POSITIVE_CONTROL.value]
GRNA_TYPE_TARGETING = GRNA_TYPE_FACET_VALUES[GrnaType.TARGETING.value]

PROMOTER_FACET = Facet.objects.get(name=DNAFeature.Facet.PROMOTER.value)
PROMOTER_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=PROMOTER_FACET.id).all()}
PROMOTER_PROMOTER = PROMOTER_FACET_VALUES[PromoterType.PROMOTER.value]
PROMOTER_NON_PROMOTER = PROMOTER_FACET_VALUES[PromoterType.NON_PROMOTER.value]

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


class FeatureOverlap(Enum):
    BEFORE = 1
    OVERLAP = 2
    AFTER = 3


@dataclass
class CCREFeature:
    _id: int
    accession_id: str
    chrom_name: str
    location: NumericRange
    cell_line: str
    closest_gene_id: int
    closest_gene_distance: int
    closest_gene_name: str
    closest_gene_ensembl_id: int
    source_file_id: int
    genome_assembly: str
    experiment_accession_id: str
    feature_type: DNAFeatureType
    genome_assembly_patch: str = "0"
    parent: Optional["CCREFeature"] = None
    misc: dict = field(default_factory=lambda: {"pseudo": True})

    def __lt__(self, other) -> bool:
        if not isinstance(other, CCREFeature):
            return NotImplemented

        if self.chrom_name < other.chrom_name:
            return True

        if self.location.lower < other.location.lower:
            return True

        if self.location.upper < other.location.upper:
            return True

        return False

    def ccre_assoc_id(self) -> int:
        if self.parent is not None:
            return self.parent._id

        return self._id

    def ccre_assoc_loc(self) -> NumericRange:
        if self.parent is not None:
            return self.parent.location

        return self.location

    def ccre_comp(self, ccre) -> FeatureOverlap:
        _, ccre_chrom_name, ccre_loc = ccre
        if self.chrom_name < ccre_chrom_name:
            return FeatureOverlap.BEFORE

        if self.chrom_name > ccre_chrom_name:
            return FeatureOverlap.AFTER

        # chrom names are equal, lets check coordinates

        if self.location.upper <= ccre_loc.lower:
            return FeatureOverlap.BEFORE

        if self.location.lower >= ccre_loc.upper:
            return FeatureOverlap.AFTER

        return FeatureOverlap.OVERLAP


def get_ccres(genome_assembly) -> list[tuple[int, str, NumericRange]]:
    if genome_assembly not in ["GRCh37", "GRCh38"]:
        raise ValueError("Please enter either GRCh37 or GRCh38 for the assembly")

    return (
        DNAFeature.objects.filter(feature_type="DNAFeatureType.CCRE", ref_genome=genome_assembly)
        .order_by("chrom_name", Func(F("location"), function="lower"), Func(F("location"), function="upper"))
        .values_list("id", "chrom_name", "location")
        .all()
    )


class Experiment:
    metadata: ExperimentMetadata
    features: Optional[list[FeatureRow]] = None
    parent_features: Optional[list[FeatureRow]] = None
    accession_id: Optional[str] = None

    def __init__(self, metadata: ExperimentMetadata):
        self.metadata = metadata

    def load(self, load_function):
        feature_rows, parent_rows = load_function(self.metadata)
        self.features = feature_rows
        self.parent_features = parent_rows

        return self

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

                parent = parents.get(feature.parent_name) if parents is not None else None
                if parent is not None:
                    parent_id, parent_accession_id = (parent._id, parent.accession_id)
                else:
                    parent_id, parent_accession_id = (None, None)

                db_ids[feature.name] = CCREFeature(
                    _id=feature_id,
                    accession_id=accession_id,
                    chrom_name=feature.chrom_name,
                    location=feature_location,
                    cell_line=feature.cell_line,
                    closest_gene_id=closest_gene["id"],
                    closest_gene_distance=distance,
                    closest_gene_name=gene_name,
                    closest_gene_ensembl_id=closest_gene_ensembl_id,
                    source_file_id=source_file_id,
                    genome_assembly=feature.genome_assembly,
                    experiment_accession_id=experiment_accession_id,
                    feature_type=DNAFeatureType(feature.feature_type),
                    parent=parent,
                )

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

    def _save_ccres(self, features: list[CCREFeature], accession_ids):
        features.sort()
        ccres = get_ccres(self.metadata.tested_elements_file.genome_assembly)
        new_ccres = StringIO()
        ccre_associations = StringIO()

        f_idx = 0  # features list index
        c_idx = 0  # ccre list index
        with FeatureIds() as ccre_ids:
            # To associate features with cCREs we need two lists -- The list of all current cCREs for a genome
            # assembly and the the list of features. These two lists must be sorted, and must be sorted in the
            # same manner.
            #
            # We work our way through both lists linearly, on each iteration moving forward on one or the other
            # (but not both). Which list we move forward on depends on the comparison between the current ccre
            # and current feature.
            # If the current feature is AFTER the current cCRE we just advance to the next cCRE.
            # If the current feature is BEFORE the current cCRE, then we create a new pseudo-cCRE from that
            # feature. The new pseudo-cCRE get associated with the current feature. We then advance to the next
            # feature.
            # If the current feature OVERLAPS with this current cCRE then we associate the feature with the cCRE.
            # Afterwards we look ahead to see if we advance the feature or the cCRE. If the feature also overlaps
            # the next cCRE we advance the cCRE -- this way if a feature overlaps multiple cCREs it will be
            # associated with all of them. Otherwise we advance to the next feature.
            #
            # If we get through all the features without getting through the cCREs, then we're done. If we get
            # through all the cCREs without getting through all the features then we have to make new psudeo-cCREs
            # with the remaining features, and do the association.
            #
            # Once we're through the lists we save all the new pseudo-cCREs and then the associations.
            #
            # By sorting the lists and advancing through only one at a time we can be sure to catch all the matches
            # without incurring massive algorithmic overhead. This is an O(n+m) algorithm, modulo the list sorting.
            while True:
                if f_idx >= len(features):
                    # We're done, we associated all the features with cCREs.
                    break

                if c_idx >= len(ccres):
                    # We got through all the existing cCREs so we have to create new pseudo-cCREs from
                    # all the remaining features.
                    for feature in features[f_idx:]:
                        ccre_id = ccre_ids.next_id()
                        new_ccres.write(
                            feature_entry(
                                id_=ccre_id,
                                accession_id=accession_ids.incr(AccessionType.CCRE),
                                cell_line=feature.cell_line,
                                chrom_name=feature.chrom_name,
                                closest_gene_id=feature.closest_gene_id,
                                closest_gene_distance=feature.closest_gene_distance,
                                closest_gene_name=feature.closest_gene_name,
                                closest_gene_ensembl_id=feature.closest_gene_ensembl_id,
                                location=feature.ccre_assoc_loc(),
                                genome_assembly=feature.genome_assembly,
                                genome_assembly_patch=feature.genome_assembly_patch,
                                misc=feature.misc,
                                feature_type=DNAFeatureType.CCRE,
                                source_file_id=feature.source_file_id,
                                experiment_accession_id=feature.experiment_accession_id,
                            )
                        )
                        ccre_associations.write(ccre_associate_entry(feature.ccre_assoc_id(), ccre_id))
                    break

                feature = features[f_idx]
                ccre = ccres[c_idx]

                match feature.ccre_comp(ccre):
                    case FeatureOverlap.BEFORE:
                        ccre_id = ccre_ids.next_id()
                        new_ccres.write(
                            feature_entry(
                                id_=ccre_id,
                                accession_id=accession_ids.incr(AccessionType.CCRE),
                                cell_line=feature.cell_line,
                                chrom_name=feature.chrom_name,
                                closest_gene_id=feature.closest_gene_id,
                                closest_gene_distance=feature.closest_gene_distance,
                                closest_gene_name=feature.closest_gene_name,
                                closest_gene_ensembl_id=feature.closest_gene_ensembl_id,
                                location=feature.ccre_assoc_loc(),
                                genome_assembly=feature.genome_assembly,
                                genome_assembly_patch=feature.genome_assembly_patch,
                                misc=feature.misc,
                                feature_type=DNAFeatureType.CCRE,
                                source_file_id=feature.source_file_id,
                                experiment_accession_id=feature.experiment_accession_id,
                            )
                        )
                        ccre_associations.write(ccre_associate_entry(feature.ccre_assoc_id(), ccre_id))
                        f_idx += 1
                    case FeatureOverlap.AFTER:
                        c_idx += 1
                    case FeatureOverlap.OVERLAP:
                        ccre_associations.write(ccre_associate_entry(feature.ccre_assoc_id(), ccre[0]))

                        if c_idx < (len(ccres) - 1) and feature.ccre_comp(ccres[c_idx + 1]) == FeatureOverlap.OVERLAP:
                            c_idx += 1
                        else:
                            f_idx += 1

        bulk_feature_save(new_ccres)
        bulk_save_associations(ccre_associations)

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
                features = self._save_features(self.features, accession_ids, feature_file.id_, parents)
                self._save_ccres(list(features.values()), accession_ids)

        return self

    def delete(self):
        """Only run delete if you want to delete the experiment, all
        associated reg effects, and any DNAFeatures created from the DB.
        Please note that it won't reset DB id numbers, so running this script with
        delete() uncommented is not, strictly, idempotent."""

        experiment = ExperimentModel.objects.get(accession_id=self.metadata.accession_id)
        DNAFeature.objects.filter(experiment_accession=experiment).delete()
        self.metadata.db_del()
