#!/bin/sh
EXPERIMENT_FILE=$1
ANALYSIS_FILE=$2

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000003_load_klann_2021_wgceres_experiment; DCPEXPR0000000003_load_klann_2021_wgceres_experiment.run(\"${EXPERIMENT_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000003_load_klann_2021_wgceres_analysis; DCPEXPR0000000003_load_klann_2021_wgceres_analysis.run(\"${ANALYSIS_FILE}\")"
