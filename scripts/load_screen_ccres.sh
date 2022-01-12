#!/bin/sh
INPUT_FILE=$1
GENOME=${2:-GRCh38}
PATCH=${3:-}

python manage.py shell -c "from scripts import load_screen_ccres; load_screen_ccres.run(\"$INPUT_FILE\", \"${GENOME}\", \"${PATCH}\")"
