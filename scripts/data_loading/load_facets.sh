#!/bin/bash
set -euo pipefail

INPUT_FILE=$1

python manage.py shell -c "from scripts.data_loading import load_facets; load_facets.run(\"$INPUT_FILE\")"
