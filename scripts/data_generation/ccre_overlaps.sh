#!/usr/bin/env bash
set -euo pipefail

# Requires bedtools (https://bedtools.readthedocs.io/en/latest/)

# The file a .bed of DHS locations is generated from
DATA_FILE=$1

ASSEMBLY=$2


# The locations of the
SOURCE_NAME_COL=$3
SOURCE_START_COL=$4
SOURCE_END_COL=$5

# This will have each DHS from $DATA_FILE matched to one or more
# cCREs from $CCRE_BED_FILE
OUTPUT_FILE=$6

# The .bed of of cCREs
CCRE_BED_FILE="ccre.bed"
python scripts/data_generation/ccre_bed.py -a ${ASSEMBLY} -o ${CCRE_BED_FILE}

PYTHONPATH=`pwd` python scripts/data_generation/source_loc_extractor.py -i ${DATA_FILE} -o out.bed --chr_name_col ${SOURCE_NAME_COL} --chr_start_col ${SOURCE_START_COL} --chr_end_col ${SOURCE_END_COL}
sort -k1,1 -k2,2n out.bed | uniq > a.bed
bedtools intersect -wo -sorted -a a.bed -b ${CCRE_BED_FILE} > ${OUTPUT_FILE}
rm out.bed a.bed ${CCRE_BED_FILE}
