#!/bin/sh
set -euo pipefail

gen_data() {
    local EXPERIMENT=$1
    local GENOME=$2
    local OUTPUT_DIR=$3

    # Install cov_viz from github: https://github.com/ReddyLab/cov_viz
    # Install cov_viz_manifest from github: https://github.com/ReddyLab/cov_viz_manifest
    # cov_viz and cov_viz_manifest require rust, which can be downloaded/installed from https://www.rust-lang.org

    cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME}
    cov_viz_manifest ${GENOME} ${OUTPUT_DIR}/level1.bin ${OUTPUT_DIR}
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
}

gen_data DCPEXPR00000001 GRCH37 ./cegs_portal/static_data/search/experiments/DCPEXPR00000001
gen_data DCPEXPR00000002 GRCH37 ./cegs_portal/static_data/search/experiments/DCPEXPR00000002

# gen_data DCPEXPR00000003 needs some changes to the cov_viz and related programs to work. Some
# of the  REOs have null effect sizes because the "direction" of the effect is "both". Deferring
# for now. It's also not clear how to surface that in the facet filter.
# gen_data DCPEXPR00000003 GRCH37 ./cegs_portal/static_data/search/experiments/DCPEXPR00000003

gen_data DCPEXPR00000004 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR00000004
gen_data DCPEXPR00000005 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR00000005
gen_data DCPEXPR00000006 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR00000006
gen_data DCPEXPR00000007 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR00000007
gen_data DCPEXPR00000008 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR00000008
gen_data DCPEXPR00000009 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR00000009
