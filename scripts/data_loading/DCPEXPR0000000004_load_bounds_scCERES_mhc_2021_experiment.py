import csv
from io import StringIO

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

from . import bulk_feature_facet_save, bulk_feature_save, get_closest_gene

GRNA_TYPE_FACET = Facet.objects.get(name="gRNA Type")
GRNA_TYPE_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=GRNA_TYPE_FACET.id).all()}
GRNA_TYPE_POS_CTRL = GRNA_TYPE_FACET_VALUES["Positive Control"]
GRNA_TYPE_TARGETING = GRNA_TYPE_FACET_VALUES["Targeting"]

PROMOTER_FACET = Facet.objects.get(name="Promoter Classification")
PROMOTER_FACET_VALUES = {facet.value: facet for facet in FacetValue.objects.filter(facet_id=PROMOTER_FACET.id).all()}
PROMOTER_PROMOTER = PROMOTER_FACET_VALUES["Promoter"]
PROMOTER_NON_PROMOTER = PROMOTER_FACET_VALUES["Non-promoter"]


@timer("Load gRNAs")
def load_grnas(
    grna_file, closest_ccre_filename, accession_ids, experiment, region_source, cell_line, ref_genome, delimiter=","
):
    reader = csv.DictReader(grna_file, delimiter=delimiter, quoting=csv.QUOTE_NONE)
    new_grnas = {}
    grnas = StringIO()
    grna_type_facets = StringIO()
    grna_promoter_facets = StringIO()
    new_dhss: dict[str, int] = {}
    dhss = StringIO()
    region_source_id = region_source.id
    experiment_accession_id = experiment.accession_id

    with FeatureIds() as feature_ids:
        for i, line in enumerate(reader):
            # every other line in this file is basically a duplicate of the previous line
            if i % 2 == 0:
                continue

            grna_id = line["grna"]
            grna_type = line["type"]
            grna_promoter_class = line["annotation_manual"]

            dhs_chrom_name = line["dhs.chr"]

            # skip DHSs associated with non-targeting guides
            if dhs_chrom_name.startswith("chr"):
                dhs_start = int(line["dhs.start"])
                dhs_end = int(line["dhs.end"])
                dhs_location = f"[{dhs_start},{dhs_end})"

                dhs_name = f"{dhs_chrom_name}:{dhs_location}"

                if dhs_name not in new_dhss:
                    closest_gene, distance, gene_name = get_closest_gene(ref_genome, dhs_chrom_name, dhs_start, dhs_end)
                    closest_gene_ensembl_id = closest_gene["ensembl_id"] if closest_gene is not None else None
                    dhs_feature_id = feature_ids.next_id()
                    dhss.write(
                        f"{dhs_feature_id}\t{accession_ids.incr(AccessionType.DHS)}\t{cell_line}\t{dhs_chrom_name}\t{closest_gene['id']}\t{distance}\t{gene_name}\t{closest_gene_ensembl_id}\t{dhs_location}\t{ref_genome}\t0\t{DNAFeatureType.DHS}\t{region_source_id}\t{experiment_accession_id}\t\\N\tfalse\ttrue\n"
                    )
                    new_dhss[dhs_name] = dhs_feature_id
                else:
                    dhs_feature_id = new_dhss[dhs_name]

            if grna_id not in new_grnas:
                grna_info = grna_id.split("-")

                # Skip non-targeting guides
                if not grna_info[0].startswith("chr"):
                    continue

                feature_id = feature_ids.next_id()

                if len(grna_info) == 5:
                    chrom_name, grna_start_str, grna_end_str, strand, _grna_seq = grna_info
                elif len(grna_info) == 6:
                    chrom_name, grna_start_str, grna_end_str, _x, _y, _grna_seq = grna_info
                    strand = "-"

                if grna_type == "targeting":
                    grna_type_facets.write(f"{feature_id}\t{GRNA_TYPE_TARGETING.id}\n")
                elif grna_type.startswith("positive_control") == "":
                    grna_type_facets.write(f"{feature_id}\t{GRNA_TYPE_POS_CTRL.id}\n")

                if grna_promoter_class == "promoter":
                    grna_promoter_facets.write(f"{feature_id}\t{PROMOTER_PROMOTER.id}\n")
                else:
                    grna_promoter_facets.write(f"{feature_id}\t{PROMOTER_NON_PROMOTER.id}\n")

                if grna_type == "targeting":
                    grna_start = int(grna_start_str)
                    grna_end = int(grna_end_str)
                else:
                    if strand == "+":
                        grna_start = int(grna_start_str)
                        grna_end = int(grna_start_str) + 20
                    elif strand == "-":
                        grna_start = int(grna_end_str) - 20
                        grna_end = int(grna_end_str)

                if strand == "+":
                    grna_location = f"[{grna_start},{grna_end})"
                elif strand == "-":
                    grna_location = f"({grna_start},{grna_end}]"

                closest_gene, distance, gene_name = get_closest_gene(ref_genome, chrom_name, grna_start, grna_end)
                closest_gene_ensembl_id = closest_gene["ensembl_id"] if closest_gene is not None else None

                grnas.write(
                    f"{feature_id}\t{accession_ids.incr(AccessionType.GRNA)}\t{cell_line}\t{chrom_name}\t{closest_gene['id']}\t{distance}\t{gene_name}\t{closest_gene_ensembl_id}\t{grna_location}\t{ref_genome}\t0\t{DNAFeatureType.GRNA}\t{region_source_id}\t{experiment_accession_id}\t{dhs_feature_id}\tfalse\ttrue\n"
                )
                guide = CcreSource(
                    _id=feature_id,
                    chrom_name=chrom_name,
                    location=grna_location,
                    cell_line=cell_line,
                    closest_gene_id=closest_gene["id"],
                    closest_gene_distance=distance,
                    closest_gene_name=gene_name,
                    closest_gene_ensembl_id=closest_gene["ensembl_id"] if closest_gene is not None else None,
                    source_file_id=region_source_id,
                    ref_genome=ref_genome,
                    experiment_accession_id=experiment_accession_id,
                )
                new_grnas[grna_id] = guide

    bulk_feature_save(dhss)
    bulk_feature_save(grnas)
    bulk_feature_facet_save(grna_type_facets)
    bulk_feature_facet_save(grna_promoter_facets)

    associate_ccres(closest_ccre_filename, new_grnas.values(), ref_genome, accession_ids)


def unload_experiment(experiment_metadata):
    try:
        print(experiment_metadata.accession_id)
        experiment = Experiment.objects.get(accession_id=experiment_metadata.accession_id)
    except Experiment.DoesNotExist:
        return
    except Exception as e:
        raise e

    DNAFeature.objects.filter(experiment_accession=experiment).delete()
    experiment_metadata.db_del()


def check_filename(experiment_filename: str):
    if len(experiment_filename) == 0:
        raise ValueError(f"scCERES experiment filename '{experiment_filename}' must not be blank")


def run(experiment_filename, closest_ccre_filename):
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
        for grna_file, file_info, delimiter in experiment_metadata.metadata():
            load_grnas(
                grna_file,
                closest_ccre_filename,
                accession_ids,
                experiment,
                experiment.files.all()[0],
                experiment_metadata.biosamples[0].cell_line,
                file_info.misc["ref_genome"],
                delimiter,
            )
