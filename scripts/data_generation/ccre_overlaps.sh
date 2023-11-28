#!/usr/bin/env bash
set -euo pipefail

# Requires bedtools (https://bedtools.readthedocs.io/en/latest/)

# The file a .bed of DHS locations is generated from
DATA_FILE=$1

# The .bed of of cCREs
CCRE_BED_FILE=$2

# The locations of the
SOURCE_NAME_COL=$3
SOURCE_START_COL=$4
SOURCE_END_COL=$5

# This will have each DHS from $DATA_FILE matched to one or more
# cCREs from $CCRE_BED_FILE
OUTPUT_FILE=$6

PYTHONPATH=`pwd` python scripts/data_generation/source_loc_extractor.py -i ${DATA_FILE} -o out.bed --chr_name_col ${SOURCE_NAME_COL} --chr_start_col ${SOURCE_START_COL} --chr_end_col ${SOURCE_END_COL}
sort -k1,1 -k2,2n out.bed | uniq > a.bed
sort -k1,1 -k2,2n ${CCRE_BED_FILE} > b.bed
bedtools intersect -wo -sorted -a a.bed -b b.bed > ${OUTPUT_FILE}
rm out.bed a.bed b.bed
