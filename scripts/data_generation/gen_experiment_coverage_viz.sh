#!/usr/bin/env bash
set -euo pipefail

gen_dir() {
    local DIR=$1

    if [ ! -x "${DIR}" ]; then
        mkdir -p "${DIR}"
    fi
}

gen_data() {
    local ANALYSIS=$1
    local GENOME=$2
    local OUTPUT_DIR="${3}/${ANALYSIS}"
    local DEFAULT_FACETS=$4

    echo $ANALYSIS
    gen_dir "${OUTPUT_DIR}"

    # Install cov_viz from github: https://github.com/ReddyLab/cov_viz
    # Install cov_viz_manifest from github: https://github.com/ReddyLab/cov_viz_manifest
    # cov_viz and cov_viz_manifest require rust, which can be downloaded/installed from https://www.rust-lang.org

    if [ $GENOME == "GRCH37" ]; then
        cp "./scripts/data_generation/data/grch37.json" $OUTPUT_DIR
    fi

    if [ $GENOME == "GRCH38" ]; then
        cp "./scripts/data_generation/data/grch38.json" $OUTPUT_DIR
    fi

    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME}
    cov_viz_manifest ${GENOME} ${OUTPUT_DIR}/level1.ecd ${OUTPUT_DIR} ${DEFAULT_FACETS}
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr1
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr2
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr3
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr4
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr5
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr6
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr7
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr8
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr9
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr10
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr11
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr12
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr13
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr14
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr15
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr16
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr17
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr18
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr19
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr20
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr21
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chr22
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chrX
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chrY
    cov_viz ${OUTPUT_DIR} ${ANALYSIS} ${GENOME} 100000 chrMT
}

default_facets=`python manage.py shell -c "from cegs_portal.search.models import FacetValue; print(' '.join(str(facet.id) for facet in FacetValue.objects.filter(value__in=['Depleted Only', 'Enriched Only', 'Mixed']).all()))"`

gen_data DCPAN0000000000 GRCH37 ./cegs_portal/static_data/search/experiments/DCPEXPR0000000002 "${default_facets}"

# gen_data DCPEXPR0000000003 needs some changes to the cov_viz and related programs to work. Some
# of the  REOs have null effect sizes because the "direction" of the effect is "both". Deferring
# for now. It's also not clear how to surface that in the facet filter.
# gen_data DCPAN0000000001 GRCH37 ./cegs_portal/static_data/search/experiments/DCPEXPR0000000003 "${default_facets}"

gen_data DCPAN0000000002 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR0000000004 "${default_facets}"
gen_data DCPAN0000000003 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR0000000005 "${default_facets}"
gen_data DCPAN0000000004 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR0000000006 "${default_facets}"
gen_data DCPAN0000000005 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR0000000007 "${default_facets}"
gen_data DCPAN0000000006 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR0000000008 "${default_facets}"
gen_data DCPAN0000000007 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR0000000009 "${default_facets}"
