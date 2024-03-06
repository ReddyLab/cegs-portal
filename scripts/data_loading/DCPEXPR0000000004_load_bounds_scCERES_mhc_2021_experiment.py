import csv

from utils.experiment import ExperimentMetadata

from .DCPEXPR0000000004_utils import grna_loc
from .load_experiment import Experiment, FeatureRow
from .types import FeatureType, GrnaFacet, PromoterFacet


def get_features(experiment_metadata: ExperimentMetadata):
    new_grnas: dict[str, FeatureRow] = {}
    new_dhss: dict[str, FeatureRow] = {}

    dhs_file = experiment_metadata.tested_elements_parent_file
    dhs_cell_line = dhs_file.biosample.cell_line

    grna_file = experiment_metadata.tested_elements_file
    grna_cell_line = grna_file.biosample.cell_line

    feature_tsv = open(grna_file.filename, "r")
    reader = csv.DictReader(feature_tsv, delimiter=grna_file.delimiter(), quoting=csv.QUOTE_NONE)

    for i, line in enumerate(reader):
        # every other line in this file is basically a duplicate of the previous line
        if i % 2 == 0:
            continue

        grna_id = line["grna"]
        grna_type = line["type"]
        grna_promoter_class = line["annotation_manual"]

        grna_info = grna_id.split("-")

        # Skip non-targeting guides and guides with no assigned enhancer
        if not grna_info[0].startswith("chr") or line["dhs.chr"] == "NA":
            continue

        dhs_chrom_name = line["dhs.chr"]

        dhs_start = int(line["dhs.start"])
        dhs_end = int(line["dhs.end"])
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

        if grna_id not in new_grnas:
            chrom_name, grna_start, grna_end, grna_bounds, grna_strand = grna_loc(line)

            categorical_facets = []
            if grna_type == "targeting":
                categorical_facets.append(GrnaFacet.TARGETING)
            elif grna_type.startswith("positive_control") == "":
                categorical_facets.append(GrnaFacet.POSITIVE_CONTROL)

            if grna_promoter_class == "promoter":
                categorical_facets.append(PromoterFacet.PROMOTER)
            else:
                categorical_facets.append(PromoterFacet.NON_PROMOTER)

            new_grnas[grna_id] = FeatureRow(
                name=grna_id,
                chrom_name=chrom_name,
                location=(int(grna_start), int(grna_end), grna_bounds),
                strand=grna_strand,
                genome_assembly=grna_file.genome_assembly,
                cell_line=grna_cell_line,
                feature_type=FeatureType.GRNA,
                facets=categorical_facets,
                parent_name=dhs_row.name,
                misc={"grna": grna_id},
            )

    feature_tsv.close()
    return new_grnas.values(), new_dhss.values()


def run(experiment_filename):
    metadata = ExperimentMetadata.file_load(experiment_filename)
    Experiment(metadata).load(get_features).save()
