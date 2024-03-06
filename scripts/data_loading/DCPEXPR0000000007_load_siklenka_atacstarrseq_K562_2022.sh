#!/bin/sh
set -euo pipefail

DATA_DIR=$1
EXPERIMENT_FILE=${DATA_DIR}/DCPEXPR0000000007_siklenka_atac-starr-seq_K562_2022/experiment.json
ANALYSIS_FILE=${DATA_DIR}/DCPEXPR0000000007_siklenka_atac-starr-seq_K562_2022/analysis001.json

echo "Loading DCPEXPR0000000007"

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000007_load_siklenka_atacstarrseq_K562_2022_experiment; DCPEXPR0000000007_load_siklenka_atacstarrseq_K562_2022_experiment.run(\"${EXPERIMENT_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000007_load_siklenka_atacstarrseq_K562_2022_analysis; DCPEXPR0000000007_load_siklenka_atacstarrseq_K562_2022_analysis.run(\"${ANALYSIS_FILE}\")"
