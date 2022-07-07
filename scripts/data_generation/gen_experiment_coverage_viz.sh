#!/bin/sh
set -euo pipefail

EXPERIMENT=$1
GENOME=$2
OUTPUT_DIR=$3

# Install cov_viz from github: https://github.com/ReddyLab/cov_viz
# cov_viz requires rust, which can be downloaded/installed from https://www.rust-lang.org

cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME}
# I think gen_experiment_coverage_manifest needs to be rewritten in rust as well
# python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_manifest; gen_experiment_coverage_manifest.run(\"$OUTPUT_DIR\", \"$GENOME\")"
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr1
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr2
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr3
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr4
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr5
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr6
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr7
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr8
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr9
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr10
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr11
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr12
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr13
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr14
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr15
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr16
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr17
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr18
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr19
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr20
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr21
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chr22
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chrX
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chrY
cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME} 100000 chrMT
