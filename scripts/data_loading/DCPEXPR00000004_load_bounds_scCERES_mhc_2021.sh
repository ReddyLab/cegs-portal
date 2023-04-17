#!/bin/sh
EXPERIMENT_FILE=$1
ANALYSIS_FILE=$2

python manage.py shell -c "from scripts.data_loading import DCPEXPR00000004_load_bounds_scCERES_mhc_2021_experiment; DCPEXPR00000004_load_bounds_scCERES_mhc_2021_experiment.run(\"${EXPERIMENT_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR00000004_load_bounds_scCERES_mhc_2021_analysis; DCPEXPR00000004_load_bounds_scCERES_mhc_2021_analysis.run(\"${ANALYSIS_FILE}\")"
