import csv

from utils.experiment import ExperimentMetadata

from .load_experiment import Experiment, FeatureRow
from .types import FeatureType, GrnaFacet

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


def read_dhss(dhs_filename):
    dhss = {}
    with open(dhs_filename, "r") as dhs_file:
        reader = csv.DictReader(dhs_file, delimiter="\t", quoting=csv.QUOTE_NONE)
        for line in reader:
            dhss[line["grna_id"]] = (line["dhs_chrom"], int(line["dhs_start"]), int(line["dhs_end"]))
    return dhss


def get_features(experiment_metadata: ExperimentMetadata):
    new_grnas: dict[str, FeatureRow] = {}
    new_dhss: dict[str, FeatureRow] = {}

    dhs_file = experiment_metadata.tested_elements_parent_file
    dhs_info = read_dhss(dhs_file.filename)
    dhs_cell_line = dhs_file.biosample.cell_line

    grna_file = experiment_metadata.tested_elements_file
    grna_cell_line = grna_file.biosample.cell_line

    feature_tsv = open(grna_file.filename, "r")
    reader = csv.DictReader(feature_tsv, delimiter=grna_file.delimiter(), quoting=csv.QUOTE_NONE)
    for line in reader:
        target_gene = line["target_gene"]

        if target_gene in TRIM_GENE_NAMES:
            target_gene = target_gene[:-2]

        # Create DHS associated with gRNA
        dhs_chrom_name, dhs_start, dhs_end = dhs_info[line["grna"]]
        dhs_location = f"[{dhs_start},{dhs_end})"
        dhs_name = f"{dhs_chrom_name}:{dhs_location}"

        if dhs_name not in new_dhss:
            new_dhss[dhs_name] = FeatureRow(
                name=dhs_name,
                chrom_name=dhs_chrom_name,
                location=(int(dhs_start), int(dhs_end), "[)"),
                genome_assembly=dhs_file.genome_assembly,
                cell_line=dhs_cell_line,
                feature_type=FeatureType.DHS,
            )

        dhs_row = new_dhss[dhs_name]

        grna_id = line["grna"]
        if grna_id not in new_grnas:
            strand = line["Strand"]
            chrom_name = line["chr"]
            grna_start = int(line["start"])
            grna_end = int(line["end"])

            if strand == "+":
                bounds = "[)"
            elif strand == "-":
                bounds = "(]"

            new_grnas[grna_id] = FeatureRow(
                name=grna_id,
                chrom_name=chrom_name,
                location=(int(grna_start), int(grna_end), bounds),
                strand=strand,
                genome_assembly=grna_file.genome_assembly,
                cell_line=grna_cell_line,
                feature_type=FeatureType.GRNA,
                facets=[GrnaFacet.TARGETING],
                parent_name=dhs_row.name,
                misc={"grna": grna_id},
            )

    feature_tsv.close()
    return new_grnas.values(), new_dhss.values()


def run(experiment_filename):
    metadata = ExperimentMetadata.file_load(experiment_filename)
    Experiment(metadata).load(get_features).save()
