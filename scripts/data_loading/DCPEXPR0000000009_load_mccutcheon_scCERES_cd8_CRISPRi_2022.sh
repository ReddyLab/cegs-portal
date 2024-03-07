#!/bin/sh
set -euo pipefail

DATA_DIR=$1
EXPERIMENT_FILE=${DATA_DIR}/DCPEXPR0000000009_mccutcheon_scCERES_cd8_CRISPRi_2022/experiment.json
ANALYSIS_FILE=${DATA_DIR}/DCPEXPR0000000009_mccutcheon_scCERES_cd8_CRISPRi_2022/analysis001.json

echo "Loading DCPEXPR0000000009"

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022_experiment; DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022_experiment.run(\"${EXPERIMENT_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022_analysis; DCPEXPR0000000008_load_mccutcheon_scCERES_cd8_CRISPR_2022_analysis.run(\"${ANALYSIS_FILE}\")"
