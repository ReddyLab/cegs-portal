#!/bin/sh
EXPERIMENT_FILE=$1
ANALYSIS_FILE=$2


python manage.py shell -c "from scripts.data_loading import DCPEXPR00000007_load_siklenka_atacstarrseq_K562_2022_experiment; DCPEXPR00000007_load_siklenka_atacstarrseq_K562_2022_experiment.run(\"${EXPERIMENT_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR00000007_load_siklenka_atacstarrseq_K562_2022_analysis; DCPEXPR00000007_load_siklenka_atacstarrseq_K562_2022_analysis.run(\"${ANALYSIS_FILE}\")"
