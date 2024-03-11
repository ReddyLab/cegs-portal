#!/bin/sh
set -euo pipefail

DATA_DIR=$1

EXPERIMENT_FILE=${DATA_DIR}/DCPEXPR0000000002_klann_scCERES_K562_2021/experiment.json
ANALYSIS_FILE=${DATA_DIR}/DCPEXPR0000000002_klann_scCERES_K562_2021/analysis001.json
CLOSEST_CCRE_FILE=${DATA_DIR}/DCPEXPR0000000002_klann_scCERES_K562_2021/dhs_bed_klann_2021_scceres_closest_ccres.txt

echo "Loading DCPEXPR0000000002"

# generate ccre overlaps
./scripts/data_generation/ccre_overlaps.sh \
    ${DATA_DIR}/DCPEXPR0000000002_klann_scCERES_K562_2021/supplementary_table_17_grna.de.markers.all.filtered.empirical_pvals.w_gene_info.csv \
    GRCh37 \
    dhs_chrom dhs_start dhs_end \
    ${CLOSEST_CCRE_FILE}


python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000002_load_klann_2021_scceres_experiment; DCPEXPR0000000002_load_klann_2021_scceres_experiment.run(\"${EXPERIMENT_FILE}\", \"${CLOSEST_CCRE_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000002_load_klann_2021_scceres_analysis; DCPEXPR0000000002_load_klann_2021_scceres_analysis.run(\"${ANALYSIS_FILE}\")"

rm ${CLOSEST_CCRE_FILE}
