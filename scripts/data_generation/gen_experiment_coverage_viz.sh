#!/bin/bash
set -euo pipefail

gen_dir() {
    local DIR=$1

    if [ ! -x "${DIR}" ]; then
        mkdir -p "${DIR}"
    fi
}

gen_data() {
    local EXPERIMENT=$1
    local GENOME=$2
    local OUTPUT_DIR=$3
    local DEFAULT_FACETS=$4

    echo $EXPERIMENT
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

    cov_viz ${OUTPUT_DIR} ${EXPERIMENT} ${GENOME}
    cov_viz_manifest ${GENOME} ${OUTPUT_DIR}/level1.bin ${OUTPUT_DIR} ${DEFAULT_FACETS}
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

default_facets=`python manage.py shell -c "from cegs_portal.search.models import FacetValue; print(' '.join(str(facet.id) for facet in FacetValue.objects.filter(value__in=['Depleted Only', 'Enriched Only', 'Mixed']).all()))"`

gen_data DCPEXPR00000001 GRCH37 ./cegs_portal/static_data/search/experiments/DCPEXPR00000001 "${default_facets}"
gen_data DCPEXPR00000002 GRCH37 ./cegs_portal/static_data/search/experiments/DCPEXPR00000002 "${default_facets}"

# gen_data DCPEXPR00000003 needs some changes to the cov_viz and related programs to work. Some
# of the  REOs have null effect sizes because the "direction" of the effect is "both". Deferring
# for now. It's also not clear how to surface that in the facet filter.
# gen_data DCPEXPR00000003 GRCH37 ./cegs_portal/static_data/search/experiments/DCPEXPR00000003 "${default_facets}"

gen_data DCPEXPR00000004 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR00000004 "${default_facets}"
gen_data DCPEXPR00000005 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR00000005 "${default_facets}"
gen_data DCPEXPR00000006 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR00000006 "${default_facets}"
gen_data DCPEXPR00000007 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR00000007 "${default_facets}"
gen_data DCPEXPR00000008 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR00000008 "${default_facets}"
gen_data DCPEXPR00000009 GRCH38 ./cegs_portal/static_data/search/experiments/DCPEXPR00000009 "${default_facets}"
