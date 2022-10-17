#!/bin/bash
set -euo pipefail

INPUT_FILE=$1
ACCESSION_FILE=$2
GENOME=${3:-GRCh38}
PATCH=${4:-}

python manage.py shell -c "from scripts.data_loading import load_screen_ccres; load_screen_ccres.run(\"$INPUT_FILE\", \"${ACCESSION_FILE}\", \"${GENOME}\", \"${PATCH}\")"
