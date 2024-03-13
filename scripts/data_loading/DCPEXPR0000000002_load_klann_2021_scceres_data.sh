#!/bin/sh
set -euo pipefail

DATA_DIR=$1

EXPERIMENT_FILE=${DATA_DIR}/DCPEXPR0000000002_klann_scCERES_K562_2021/experiment.json
ANALYSIS_FILE=${DATA_DIR}/DCPEXPR0000000002_klann_scCERES_K562_2021/analysis001.json

echo "Loading DCPEXPR0000000002"

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000002_load_klann_2021_scceres_experiment; DCPEXPR0000000002_load_klann_2021_scceres_experiment.run(\"${EXPERIMENT_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000002_load_klann_2021_scceres_analysis; DCPEXPR0000000002_load_klann_2021_scceres_analysis.run(\"${ANALYSIS_FILE}\")"
