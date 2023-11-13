#!/bin/sh
EXPERIMENT_FILE=$1
ANALYSIS_FILE=$2

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000004_load_bounds_scCERES_mhc_2021_experiment; DCPEXPR0000000004_load_bounds_scCERES_mhc_2021_experiment.run(\"${EXPERIMENT_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000004_load_bounds_scCERES_mhc_2021_analysis; DCPEXPR0000000004_load_bounds_scCERES_mhc_2021_analysis.run(\"${ANALYSIS_FILE}\")"
