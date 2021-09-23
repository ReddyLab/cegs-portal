#!/bin/sh
INPUT_FILE=$1

python manage.py shell -c "from scripts import load_wgceres_data; load_wgceres_data.run(\"$INPUT_FILE\")"
