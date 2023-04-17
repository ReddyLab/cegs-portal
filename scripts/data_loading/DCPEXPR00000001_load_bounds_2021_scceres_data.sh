#!/bin/sh
set -euo pipefail

EXPERIMENT_FILE=$1
ANALYSIS_FILE=$2

python manage.py shell -c "from scripts.data_loading import DCPEXPR00000001_load_bounds_2021_scceres_experiment; DCPEXPR00000001_load_bounds_2021_scceres_experiment.run(\"${EXPERIMENT_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR00000001_load_bounds_2021_scceres_analysis; DCPEXPR00000001_load_bounds_2021_scceres_analysis.run(\"${ANALYSIS_FILE}\")"
