import csv
from io import StringIO

from psycopg2.extras import NumericRange

from cegs_portal.search.models import (
    AccessionIds,
    AccessionType,
    DNAFeature,
    DNAFeatureType,
    Experiment,
    Facet,
    FacetValue,
)
from utils import timer
from utils.ccres import CcreSource, associate_ccres
from utils.db_ids import FeatureIds
from utils.experiment import ExperimentMetadata

from . import get_closest_gene
from .db import bulk_feature_facet_save, bulk_feature_save, feature_entry

# These gene names appear in the data and have a "version" ("".1") in a few instances.
# We don't know why. It's safe to remove the version for processing though.
TRIM_GENE_NAMES = [
    "HSPA14.1",
    "MATR3.1",
    "GGT1.1",
    "TMSB15B.1",
    "TBCE.1",
    "CYB561D2.1",
    "GOLGA8M.1",
    "LINC01238.1",
    "ARMCX5-GPRASP2.1",
    "LINC01505.1",
]

GRNA_TYPE_FACET = Facet.objects.get(name="gRNA Type")
GRNA_TYPE_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=GRNA_TYPE_FACET.id).all()}
GRNA_TYPE_TARGETING = GRNA_TYPE_FACET_VALUES["Targeting"]


def load_dhss(dhs_filename):
    dhss = {}
    with open(dhs_filename, "r") as dhs_file:
        reader = csv.DictReader(dhs_file, delimiter="\t", quoting=csv.QUOTE_NONE)
        for line in reader:
            dhss[line["grna_id"]] = (
                line["dhs_chrom"],
                int(line["dhs_start"]),
                int(line["dhs_end"]),
                line["gene_symbol"],
            )
    return dhss


@timer("Load GRNAs")
def load_grnas(
    ceres_file,
    closest_ccre_filename,
    dhs_filename,
    accession_ids,
    experiment,
    region_source,
    cell_line,
    ref_genome,
    delimiter=",",
):
    reader = csv.DictReader(ceres_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    dhs_info = load_dhss(dhs_filename)
    new_grnas = {}
    grnas = StringIO()
    grna_type_facets = StringIO()
    new_dhss: dict[str, int] = {}
    new_ccre_sources: list[CcreSource] = []
    dhss = StringIO()
    region_source_id = region_source.id
    experiment_accession_id = experiment.accession_id
    with FeatureIds() as feature_ids:
        for line in reader:
            target_gene = line["target_gene"]

            if target_gene in TRIM_GENE_NAMES:
                target_gene = target_gene[:-2]

            # Create DHS associated with gRNA
            dhs_chrom_name, dhs_start, dhs_end, _ = dhs_info[line["grna"]]
            dhs_location = f"[{dhs_start},{dhs_end})"
            dhs_name = f"{dhs_chrom_name}:{dhs_location}"

            if dhs_name not in new_dhss:
                closest_gene, distance, gene_name = get_closest_gene(ref_genome, dhs_chrom_name, dhs_start, dhs_end)
                closest_gene_ensembl_id = closest_gene["ensembl_id"] if closest_gene is not None else None
                dhs_feature_id = feature_ids.next_id()
                dhs_accession_id = accession_ids.incr(AccessionType.DHS)
                dhss.write(
                    feature_entry(
                        id_=dhs_feature_id,
                        accession_id=dhs_accession_id,
                        cell_line=cell_line,
                        chrom_name=dhs_chrom_name,
                        location=dhs_location,
                        closest_gene_id=closest_gene["id"],
                        closest_gene_distance=distance,
                        closest_gene_name=gene_name,
                        closest_gene_ensembl_id=closest_gene_ensembl_id,
                        ref_genome=ref_genome,
                        feature_type=DNAFeatureType.DHS,
                        source_file_id=region_source_id,
                        experiment_accession_id=experiment_accession_id,
                    )
                )
                new_dhss[dhs_name] = (dhs_feature_id, dhs_accession_id, NumericRange(dhs_start, dhs_end, "[)"))

            dhs_feature_id, dhs_accession_id, dhs_location = new_dhss[dhs_name]

            grna_id = line["grna"]
            if grna_id not in new_grnas:
                feature_id = feature_ids.next_id()

                strand = line["Strand"]
                chrom_name = line["chr"]
                grna_start = int(line["start"])
                grna_end = int(line["end"])

                if strand == "+":
                    bounds = "[)"
                elif strand == "-":
                    bounds = "(]"

                grna_location = NumericRange(grna_start, grna_end, bounds)

                closest_gene, distance, gene_name = get_closest_gene(ref_genome, chrom_name, grna_start, grna_end)
                closest_gene_ensembl_id = closest_gene["ensembl_id"] if closest_gene is not None else None

                grnas.write(
                    feature_entry(
                        id_=feature_id,
                        accession_id=accession_ids.incr(AccessionType.GRNA),
                        cell_line=cell_line,
                        chrom_name=chrom_name,
                        location=grna_location,
                        strand=strand,
                        closest_gene_id=closest_gene["id"],
                        closest_gene_distance=distance,
                        closest_gene_name=gene_name,
                        closest_gene_ensembl_id=closest_gene_ensembl_id,
                        ref_genome=ref_genome,
                        feature_type=DNAFeatureType.GRNA,
                        parent_id=dhs_feature_id,
                        parent_accession_id=dhs_accession_id,
                        source_file_id=region_source_id,
                        experiment_accession_id=experiment_accession_id,
                        misc={"grna": grna_id},
                    )
                )
                new_ccre_sources.append(
                    CcreSource(
                        _id=feature_id,
                        chrom_name=chrom_name,
                        test_location=NumericRange(grna_start, grna_end, "[)"),
                        new_location=dhs_location,
                        cell_line=cell_line,
                        closest_gene_id=closest_gene["id"],
                        closest_gene_distance=distance,
                        closest_gene_name=gene_name,
                        closest_gene_ensembl_id=closest_gene_ensembl_id,
                        source_file_id=region_source_id,
                        ref_genome=ref_genome,
                        experiment_accession_id=experiment_accession_id,
                    )
                )

                grna_type_facets.write(f"{feature_id}\t{GRNA_TYPE_TARGETING.id}\n")
                new_grnas[grna_id] = feature_id

    bulk_feature_save(dhss)
    bulk_feature_save(grnas)
    bulk_feature_facet_save(grna_type_facets)

    associate_ccres(closest_ccre_filename, new_ccre_sources, ref_genome, accession_ids)


def unload_experiment(experiment_metadata):
    experiment = Experiment.objects.get(accession_id=experiment_metadata.accession_id)
    DNAFeature.objects.filter(experiment_accession=experiment).delete()
    experiment_metadata.db_del()


def check_filename(experiment_filename: str):
    if len(experiment_filename) == 0:
        raise ValueError(f"scCERES experiment filename '{experiment_filename}' must not be blank")


def run(experiment_filename, closest_ccre_filename, dhs_filename):
    with open(experiment_filename) as experiment_file:
        experiment_metadata = ExperimentMetadata.json_load(experiment_file)
    check_filename(experiment_metadata.name)

    # Only run unload_experiment if you want to delete the experiment, all
    # associated reg effects, and any DNAFeatures created from the DB.
    # Please note that it won't reset DB id numbers, so running this script with
    # unload_experiment() uncommented is not, strictly, idempotent.
    # unload_experiment(experiment_metadata)

    experiment = experiment_metadata.db_save()

    with AccessionIds(message=f"{experiment.accession_id}: {experiment.name}"[:200]) as accession_ids:
        ceres_file, file_info, _delimiter = next(experiment_metadata.metadata())
        load_grnas(
            ceres_file,
            closest_ccre_filename,
            dhs_filename,
            accession_ids,
            experiment,
            experiment.files.all()[0],
            experiment_metadata.biosamples[0].cell_line,
            file_info.misc["ref_genome"],
            "\t",
        )
