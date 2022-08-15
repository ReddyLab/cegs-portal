#!/bin/sh
set -euo pipefail

DATA_DIR=$1

# Load facets
./scripts/data_loading/load_facets.sh ${DATA_DIR}/facets/facets.tsv

# Load gencode annotations and FeatureAssemblies (genes, transcripts, exons)
./scripts/data_loading/load_gencode_gff3_data.sh ${DATA_DIR}/gencode_annotations/gencode.v19.annotation.gff3 GRCh37 '' 19
./scripts/data_loading/load_gencode_gff3_data.sh ${DATA_DIR}/gencode_annotations/gencode.v38.annotation.gff3 GRCh38 13 38

# Load cCREs from SCREEN
./scripts/data_loading/load_screen_ccres.sh ${DATA_DIR}/screen_ccres/ccres_hg19.json GRCh37 ''
./scripts/data_loading/load_screen_ccres.sh ${DATA_DIR}/screen_ccres/ccres_hg38.json GRCh38 13

# Load experiment data
./scripts/data_loading/DCPEXPR00000001_load_bounds_2021_scceres_data.sh ${DATA_DIR}/DCPEXPR00000001_bounds_scCERES_iPSC_2021/experiment.json
./scripts/data_loading/DCPEXPR00000003_load_klann_2021_wgceres_data.sh ${DATA_DIR}/DCPEXPR00000003_klann_wgCERES_K562_2021/experiment.json
./scripts/data_loading/DCPEXPR00000002_load_klann_2021_scceres_data.sh ${DATA_DIR}/DCPEXPR00000002_klann_scCERES_K562_2021/experiment.json

# Apply SCREEN cCRE categories to DHSs from DCPEXPR00000002
./scripts/data_generation/DCPEXPR00000002_dhs_bed_klann_2021_scceres.sh \
    ${DATA_DIR}/DCPEXPR00000002_klann_scCERES_K562_2021/supplementary_table_17_grna.de.markers.all.filtered.empirical_pvals.w_gene_info.csv \
    ${DATA_DIR}/screen_ccres/GRCh19-cCREs.bed \
    ${DATA_DIR}/DCPEXPR00000002_klann_scCERES_K562_2021/dhs_bed_klann_2021_scceres_closest_ccres.txt
./scripts/data_loading/DCPEXPR00000002_dhs_closest_ccres_klann_2021_scceres.sh ${DATA_DIR}/DCPEXPR00000002_klann_scCERES_K562_2021/dhs_bed_klann_2021_scceres_closest_ccres.txt

./scripts/data_loading/DCPEXPR00000004_load_bounds_scCERES_mhc_2021.sh ${DATA_DIR}/DCPEXPR00000004_bounds_scCERES_mhc_2021/experiment.json
