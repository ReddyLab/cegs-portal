#!/bin/sh
set -euo pipefail

EXPERIMENT=$1
GENOME=$2
OUTPUT_DIR=$3

python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"1\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"2\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"3\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"4\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"5\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"6\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"7\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"8\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"9\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"10\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"11\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"12\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"13\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"14\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"15\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"16\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"17\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"18\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"19\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"20\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"21\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"22\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"X\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"Y\")"
python manage.py shell -c "from scripts.data_generation import gen_experiment_coverage_viz; gen_experiment_coverage_viz.run(\"$OUTPUT_DIR\", \"$EXPERIMENT\", \"$GENOME\", 100_000, \"MT\")"
