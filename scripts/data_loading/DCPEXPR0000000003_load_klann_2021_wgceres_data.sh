#!/bin/sh
set -euo pipefail

DATA_DIR=$1

EXPERIMENT_FILE=${DATA_DIR}/DCPEXPR0000000003_klann_wgCERES_K562_2021/experiment.json
ANALYSIS_FILE=${DATA_DIR}/DCPEXPR0000000003_klann_wgCERES_K562_2021/analysis001.json
CLOSEST_CCRE_FILE=${DATA_DIR}/DCPEXPR0000000003_klann_wgCERES_K562_2021/dhs_bed_klann_2021_scceres_closest_ccres.txt

echo "Loading DCPEXPR0000000003"

# generate ccre overlaps
./scripts/data_generation/ccre_overlaps.sh \
    ${DATA_DIR}/DCPEXPR0000000003_klann_wgCERES_K562_2021/supplementary_table_5_DHS_summary_results.tsv \
    GRCh37 \
    chrom chromStart chromEnd \
    ${CLOSEST_CCRE_FILE}

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000003_load_klann_2021_wgceres_experiment; DCPEXPR0000000003_load_klann_2021_wgceres_experiment.run(\"${EXPERIMENT_FILE}\", \"${CLOSEST_CCRE_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000003_load_klann_2021_wgceres_analysis; DCPEXPR0000000003_load_klann_2021_wgceres_analysis.run(\"${ANALYSIS_FILE}\")"

rm ${CLOSEST_CCRE_FILE}
