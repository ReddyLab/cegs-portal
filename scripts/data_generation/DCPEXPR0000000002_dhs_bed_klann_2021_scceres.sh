#!/usr/bin/env bash
set -euo pipefail

# Requires bedtools (https://bedtools.readthedocs.io/en/latest/)

# The file a .bed of DHS locations is generated from
TYLER_DATA_FILE=$1

# The .bed of of cCREs
CCRE_BED_FILE=$2

# This will have each DHS from $TYLER_DATA_FILE matched to one or more
# cCREs from $CCRE_BED_FILE
OUTPUT_FILE=$3

python scripts/data_generation/DCPEXPR0000000002_dhs_bed_klann_2021_scceres.py ${TYLER_DATA_FILE} out.bed
sort -k1,1 -k2,2n out.bed | uniq > a.bed
sort -k1,1 -k2,2n ${CCRE_BED_FILE} > b.bed
bedtools closest -t all -a a.bed -b b.bed > ${OUTPUT_FILE}
rm out.bed a.bed b.bed
