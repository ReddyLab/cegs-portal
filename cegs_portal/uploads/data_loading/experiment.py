import csv
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
    Facet,
    FacetValue,
)
from utils.db_ids import FeatureIds

from .closest_gene import get_closest_gene
from .db import (
    bulk_feature_facet_save,
    bulk_feature_save,
    bulk_save_associations,
    ccre_associate_entry,
    feature_entry,
    feature_facet_entry,
)
from .metadata import ExperimentMetadata, InternetFile
from .types import (
    ChromosomeStrands,
    FeatureType,
    GenomeAssembly,
    GrnaFacet,
    PromoterFacet,
)


@dataclass
class FeatureRow:
    name: Optional[str]
    chrom_name: str
    location: tuple[int, int]  # start, end
    genome_assembly: GenomeAssembly
    cell_line: str
    feature_type: Optional[FeatureType]
    facets: list[GrnaFacet | PromoterFacet] = field(default_factory=list)
    parent_name: Optional[str] = None
    misc: Optional[Any] = None
    strand: Optional[ChromosomeStrands] = None

    def __post_init__(self):
        if self.strand == ".":
            self.strand = None


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
    genome_assembly: GenomeAssembly
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
    assert GenomeAssembly(genome_assembly)

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

        grna_type_facet = Facet.objects.get(name=DNAFeature.Facet.GRNA_TYPE.value)
        grna_type_facet_values = {
            facet.value: facet for facet in FacetValue.objects.filter(facet_id=grna_type_facet.id).all()
        }

        promoter_facet = Facet.objects.get(name=DNAFeature.Facet.PROMOTER.value)
        promoter_facet_values = {
            facet.value: facet for facet in FacetValue.objects.filter(facet_id=promoter_facet.id).all()
        }

        self.facet_values = grna_type_facet_values | promoter_facet_values

    def load(self, elements_file_location=None):
        source_type = self.metadata.source_type
        parent_source_type = self.metadata.parent_source_type

        genome_assembly = self.metadata.tested_elements_file.genome_assembly

        new_elements: dict[str, FeatureRow] = {}
        new_parent_elements: dict[str, FeatureRow] = {}

        elements_file = self.metadata.tested_elements_file
        elements_cell_line = elements_file.biosample.cell_line

        if elements_file_location is None:
            elements_tsv = InternetFile(elements_file.file_location).file
        else:
            elements_tsv = InternetFile(elements_file_location).file

        reader = csv.DictReader(elements_tsv, delimiter=elements_file.delimiter(), quoting=csv.QUOTE_NONE)

        for line in reader:
            parent_chrom, parent_start, parent_end, parent_strand = (
                line["parent_chrom"],
                line["parent_start"],
                line["parent_end"],
                line["parent_strand"],
            )

            if (parent_chrom == parent_start == parent_end == parent_strand) and (
                parent_chrom is None or parent_chrom == ""
            ):
                parent_row = None
            else:
                parent_start, parent_end = int(parent_start), int(parent_end)
                parent_name = f"{parent_chrom}:{parent_start}-{parent_end}:{parent_strand}"

                if parent_name not in new_parent_elements:
                    new_parent_elements[parent_name] = FeatureRow(
                        name=parent_name,
                        chrom_name=parent_chrom,
                        location=(parent_start, parent_end),
                        strand=parent_strand,
                        genome_assembly=GenomeAssembly(genome_assembly),
                        cell_line=elements_cell_line,
                        feature_type=FeatureType(parent_source_type) if parent_source_type is not None else None,
                    )

                parent_row = new_parent_elements[parent_name]

            element_chrom, element_start, element_end, element_strand = (
                line["chrom"],
                int(line["start"]),
                int(line["end"]),
                line["strand"],
            )
            element_name = f"{element_chrom}:{element_start}-{element_end}:{element_strand}"

            categorical_facets = (
                [f.split("=") for f in line["facets"].split(";")]
                if line["facets"] != "" and line["facets"] is not None
                else []
            )
            misc = (
                {k: v for k, v in [f.split("=") for f in line["misc"].split(";")]}
                if line["misc"] != "" and line["misc"] is not None
                else {}
            )

            new_elements[element_name] = FeatureRow(
                name=element_name,
                chrom_name=element_chrom,
                location=(element_start, element_end),
                strand=element_strand,
                genome_assembly=GenomeAssembly(genome_assembly),
                cell_line=elements_cell_line,
                feature_type=FeatureType(source_type),
                facets=categorical_facets,
                parent_name=parent_row.name if parent_row is not None else None,
                misc=misc,
            )

        elements_tsv.close()
        self.features = new_elements.values()
        if len(new_parent_elements) > 0:
            self.parent_features = new_parent_elements.values()
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
                        name=feature.name,
                        accession_id=accession_id,
                        cell_line=feature.cell_line,
                        chrom_name=feature.chrom_name,
                        location=feature_location,
                        strand=feature.strand,
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
                for _, facet_value in feature.facets:
                    feature_facets.write(
                        feature_facet_entry(feature_id=feature_id, facet_id=self.facet_values[facet_value].id)
                    )

        bulk_feature_save(feature_rows)
        bulk_feature_facet_save(feature_facets)
        return db_ids

    def _save_ccres(self, features: list[CCREFeature], accession_ids, parent_ccre_assignments: dict[int:int] = None):
        features.sort()
        ccres = get_ccres(self.metadata.tested_elements_file.genome_assembly)
        new_ccres = StringIO()
        ccre_associations = StringIO()
        features_with_associated_ccres: dict[int:int] = {}

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

                feature = features[f_idx]
                if parent_ccre_assignments is not None and feature.parent._id in parent_ccre_assignments:
                    ccre_id = parent_ccre_assignments[feature.parent._id]
                    ccre_associations.write(ccre_associate_entry(feature._id, ccre_id))
                    features_with_associated_ccres[feature._id] = ccre_id
                    f_idx += 1
                    continue

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
                                location=feature.location,
                                genome_assembly=feature.genome_assembly,
                                genome_assembly_patch=feature.genome_assembly_patch,
                                misc=feature.misc,
                                feature_type=DNAFeatureType.CCRE,
                                source_file_id=feature.source_file_id,
                                experiment_accession_id=feature.experiment_accession_id,
                            )
                        )
                        ccre_associations.write(ccre_associate_entry(feature._id, ccre_id))
                        features_with_associated_ccres[feature._id] = ccre_id
                    break

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
                                location=feature.location,
                                genome_assembly=feature.genome_assembly,
                                genome_assembly_patch=feature.genome_assembly_patch,
                                misc=feature.misc,
                                feature_type=DNAFeatureType.CCRE,
                                source_file_id=feature.source_file_id,
                                experiment_accession_id=feature.experiment_accession_id,
                            )
                        )
                        ccre_associations.write(ccre_associate_entry(feature._id, ccre_id))
                        features_with_associated_ccres[feature._id] = ccre_id
                        f_idx += 1
                    case FeatureOverlap.AFTER:
                        c_idx += 1
                    case FeatureOverlap.OVERLAP:
                        ccre_associations.write(ccre_associate_entry(feature._id, ccre[0]))
                        features_with_associated_ccres[feature._id] = ccre[0]

                        if c_idx < (len(ccres) - 1) and feature.ccre_comp(ccres[c_idx + 1]) == FeatureOverlap.OVERLAP:
                            c_idx += 1
                        else:
                            f_idx += 1

        bulk_feature_save(new_ccres)
        bulk_save_associations(ccre_associations)
        return features_with_associated_ccres

    def save(self):
        with transaction.atomic():
            experiment = self.metadata.db_save()
            self.accession_id = experiment.accession_id

            with AccessionIds(message=f"{experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
                parents = None
                parent_ccre_assignments = None
                if self.parent_features is not None:
                    parent_file = self.metadata.tested_elements_file
                    parents = self._save_features(self.parent_features, accession_ids, parent_file.id_)
                    parent_ccre_assignments = self._save_ccres(list(parents.values()), accession_ids)

                feature_file = self.metadata.tested_elements_file
                features = self._save_features(self.features, accession_ids, feature_file.id_, parents)
                self._save_ccres(list(features.values()), accession_ids, parent_ccre_assignments)

        return self


def load(experiment_filename, accession_id):
    metadata = ExperimentMetadata.load(experiment_filename, accession_id)
    Experiment(metadata).load().save()
