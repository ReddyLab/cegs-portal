#!/bin/sh
set -euo pipefail

DATA_DIR=$1

EXPERIMENT_FILE=${DATA_DIR}/DCPEXPR0000000003_klann_wgCERES_K562_2021/experiment.json
ANALYSIS_FILE=${DATA_DIR}/DCPEXPR0000000003_klann_wgCERES_K562_2021/analysis001.json

echo "Loading DCPEXPR0000000003"

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000003_load_klann_2021_wgceres_experiment; DCPEXPR0000000003_load_klann_2021_wgceres_experiment.run(\"${EXPERIMENT_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000003_load_klann_2021_wgceres_analysis; DCPEXPR0000000003_load_klann_2021_wgceres_analysis.run(\"${ANALYSIS_FILE}\")"
