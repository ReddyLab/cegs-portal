#!/bin/sh
INPUT_FILE=$1
ACCESSION_FILE=$2

python manage.py shell -c "from scripts.data_loading import DCPEXPR00000007_load_siklenka_atacstarrseq_K562_2022; DCPEXPR00000007_load_siklenka_atacstarrseq_K562_2022.run(\"${INPUT_FILE}\", \"${ACCESSION_FILE}\")"
