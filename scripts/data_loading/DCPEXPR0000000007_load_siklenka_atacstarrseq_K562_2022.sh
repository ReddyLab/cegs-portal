#!/bin/sh
set -euo pipefail

DATA_DIR=$1
EXPERIMENT_FILE=${DATA_DIR}/DCPEXPR0000000007_siklenka_atac-starr-seq_K562_2022/experiment.json
ANALYSIS_FILE=${DATA_DIR}/DCPEXPR0000000007_siklenka_atac-starr-seq_K562_2022/analysis001.json
CLOSEST_CCRE_FILE=${DATA_DIR}/DCPEXPR0000000007_siklenka_atac-starr-seq_K562_2022/closest_ccres.txt

echo "Loading DCPEXPR0000000007"

# generate ccre overlaps
./scripts/data_generation/ccre_overlaps.sh \
    ${DATA_DIR}/DCPEXPR0000000007_siklenka_atac-starr-seq_K562_2022/atacSTARR.ultra_deep.csaw.hg38.v10.common_file_formatted.tsv \
    GRCh38 \
    seqnames start end \
    ${CLOSEST_CCRE_FILE}

python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000007_load_siklenka_atacstarrseq_K562_2022_experiment; DCPEXPR0000000007_load_siklenka_atacstarrseq_K562_2022_experiment.run(\"${EXPERIMENT_FILE}\", \"${CLOSEST_CCRE_FILE}\")"
python manage.py shell -c "from scripts.data_loading import DCPEXPR0000000007_load_siklenka_atacstarrseq_K562_2022_analysis; DCPEXPR0000000007_load_siklenka_atacstarrseq_K562_2022_analysis.run(\"${ANALYSIS_FILE}\")"

rm ${CLOSEST_CCRE_FILE}
