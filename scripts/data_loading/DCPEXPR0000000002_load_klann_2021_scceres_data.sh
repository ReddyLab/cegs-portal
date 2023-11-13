#!/bin/sh
EXPERIMENT_FILE=$1
ANALYSIS_FILE=$2

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000002_load_klann_2021_scceres_experiment; DCPEXPR0000000002_load_klann_2021_scceres_experiment.run(\"${EXPERIMENT_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000002_load_klann_2021_scceres_analysis; DCPEXPR0000000002_load_klann_2021_scceres_analysis.run(\"${ANALYSIS_FILE}\")"
