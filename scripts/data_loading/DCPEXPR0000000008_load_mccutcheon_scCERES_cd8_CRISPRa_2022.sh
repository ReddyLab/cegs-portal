#!/bin/sh
set -euo pipefail

DATA_DIR=$1
EXPERIMENT_FILE=${DATA_DIR}/DCPEXPR0000000008_mccutcheon_scCERES_cd8_CRISPRa_2022/experiment.json
ANALYSIS_FILE=${DATA_DIR}/DCPEXPR0000000008_mccutcheon_scCERES_cd8_CRISPRa_2022/analysis001.json

echo "Loading DCPEXPR0000000008"

# # generate ccre overlaps
# ./scripts/data_generation/ccre_overlaps.sh \
#     ${DATA_DIR}/DCPEXPR0000000008_mccutcheon_scCERES_cd8_CRISPRa_2022/crispra.mast.volcano.all.min_thres_4.with_coords.tsv \
#     GRCh38 \
#     chr start end \
#     ${CLOSEST_CCRE_FILE}

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022_experiment; DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022_experiment.run(\"${EXPERIMENT_FILE}\")"
# python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022_analysis; DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022_analysis.run(\"${ANALYSIS_FILE}\")"
