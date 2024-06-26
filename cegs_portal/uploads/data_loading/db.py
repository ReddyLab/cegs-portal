import json
from io import StringIO
from os import SEEK_SET
from typing import Optional

from django.db import connection, transaction


def reo_entry(
    id_,
    accession_id,
    experiment_id,
    experiment_accession_id,
    analysis_accession_id,
    facet_num_values=None,
    archived="false",
    public="true",
):
    facet_num_values = "\\N" if facet_num_values is None else json.dumps(facet_num_values)
    return f"{id_}\t{accession_id}\t{experiment_id}\t{experiment_accession_id}\t{analysis_accession_id}\t{facet_num_values}\t{archived}\t{public}\n"


def bulk_reo_save(
    effects: StringIO,
    categorical_facets: StringIO,
    source_associations: StringIO,
    target_associations: Optional[StringIO] = None,
):
    with transaction.atomic(), connection.cursor() as cursor:
        effects.seek(0, SEEK_SET)
        print("Adding RegulatoryEffectObservations")
        cursor.copy_from(
            effects,
            "search_regulatoryeffectobservation",
            columns=(
                "id",
                "accession_id",
                "experiment_id",
                "experiment_accession_id",
                "analysis_accession_id",
                "facet_num_values",
                "archived",
                "public",
            ),
        )

    with transaction.atomic(), connection.cursor() as cursor:
        categorical_facets.seek(0, SEEK_SET)
        print("Adding categorical facets to effects")
        cursor.copy_from(
            categorical_facets,
            "search_regulatoryeffectobservation_facet_values",
            columns=(
                "regulatoryeffectobservation_id",
                "facetvalue_id",
            ),
        )

    with transaction.atomic(), connection.cursor() as cursor:
        source_associations.seek(0, SEEK_SET)
        print("Adding sources to RegulatoryEffectObservations")
        cursor.copy_from(
            source_associations,
            "search_regulatoryeffectobservation_sources",
            columns=("regulatoryeffectobservation_id", "dnafeature_id"),
        )

        if target_associations is not None:
            target_associations.seek(0, SEEK_SET)
            print("Adding targets to RegulatoryEffectObservations")
            cursor.copy_from(
                target_associations,
                "search_regulatoryeffectobservation_targets",
                columns=("regulatoryeffectobservation_id", "dnafeature_id"),
            )


def feature_entry(
    id_,
    accession_id,
    chrom_name,
    location,
    genome_assembly,
    feature_type,
    ids=None,
    ensembl_id="\\N",
    name=None,
    cell_line="\\N",
    closest_gene_id="\\N",
    closest_gene_distance="\\N",
    closest_gene_name="\\N",
    closest_gene_ensembl_id="\\N",
    genome_assembly_patch="0",
    feature_subtype="\\N",
    strand=None,
    source_file_id=None,
    experiment_accession_id="\\N",
    parent_id=None,
    parent_accession_id=None,
    misc=None,
    archived="false",
    public="true",
):
    ids = "\\N" if ids is None else json.dumps(ids)
    name = "\\N" if name is None else name
    misc = "\\N" if misc is None else json.dumps(misc)
    strand = "\\N" if strand is None else strand
    source_file_id = "\\N" if source_file_id is None else source_file_id
    parent_id = "\\N" if parent_id is None else parent_id
    parent_accession_id = "\\N" if parent_accession_id is None else parent_accession_id
    return f"{id_}\t{accession_id}\t{ids}\t{ensembl_id}\t{name}\t{cell_line}\t{chrom_name}\t{closest_gene_id}\t{closest_gene_distance}\t{closest_gene_name}\t{closest_gene_ensembl_id}\t{location}\t{strand}\t{genome_assembly}\t{genome_assembly_patch}\t{feature_type}\t{feature_subtype}\t{source_file_id}\t{experiment_accession_id}\t{parent_id}\t{parent_accession_id}\t{misc}\t{archived}\t{public}\n"


def feature_facet_entry(feature_id, facet_id):
    return f"{feature_id}\t{facet_id}\n"


def source_entry(reo_id, source_id):
    return f"{reo_id}\t{source_id}\n"


def target_entry(reo_id, target_id):
    return f"{reo_id}\t{target_id}\n"


def cat_facet_entry(reo_id, facet_id):
    return f"{reo_id}\t{facet_id}\n"


def ccre_associate_entry(feature_id, ccre_id):
    return f"{feature_id}\t{ccre_id}\n"


def bulk_feature_save(features: StringIO):
    features.seek(0, SEEK_SET)
    print("Adding features")
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.copy_from(
            features,
            "search_dnafeature",
            columns=(
                "id",
                "accession_id",
                "ids",
                "ensembl_id",
                "name",
                "cell_line",
                "chrom_name",
                "closest_gene_id",
                "closest_gene_distance",
                "closest_gene_name",
                "closest_gene_ensembl_id",
                "location",
                "strand",
                "ref_genome",
                "ref_genome_patch",
                "feature_type",
                "feature_subtype",
                "source_file_id",
                "experiment_accession_id",
                "parent_id",
                "parent_accession_id",
                "misc",
                "archived",
                "public",
            ),
        )


def bulk_feature_facet_save(facets):
    with transaction.atomic(), connection.cursor() as cursor:
        facets.seek(0, SEEK_SET)
        print("Adding facets to features")
        cursor.copy_from(
            facets,
            "search_dnafeature_facet_values",
            columns=(
                "dnafeature_id",
                "facetvalue_id",
            ),
        )


def bulk_save_associations(associations):
    associations.seek(0, SEEK_SET)
    print("Adding ccre associations to features")
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.copy_from(
            associations, "search_dnafeature_associated_ccres", columns=("from_dnafeature_id", "to_dnafeature_id")
        )
