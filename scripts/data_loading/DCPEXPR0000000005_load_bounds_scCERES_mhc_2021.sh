#!/bin/sh
set -euo pipefail

DATA_DIR=$1

EXPERIMENT_FILE=${DATA_DIR}/DCPEXPR0000000005_bounds_scCERES_mhc_k562_2021/experiment.json
ANALYSIS_FILE=${DATA_DIR}/DCPEXPR0000000005_bounds_scCERES_mhc_k562_2021/analysis001.json

echo "Loading DCPEXPR0000000005"

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000004_load_bounds_scCERES_mhc_2021_experiment; DCPEXPR0000000004_load_bounds_scCERES_mhc_2021_experiment.run(\"${EXPERIMENT_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000004_load_bounds_scCERES_mhc_2021_analysis; DCPEXPR0000000004_load_bounds_scCERES_mhc_2021_analysis.run(\"${ANALYSIS_FILE}\")"
