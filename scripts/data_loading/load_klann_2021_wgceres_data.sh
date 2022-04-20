#!/bin/sh
INPUT_FILE=$1

python manage.py shell -c "from scripts import load_klann_2021_wgceres_data; load_klann_2021_wgceres_data.run(\"$INPUT_FILE\")"
