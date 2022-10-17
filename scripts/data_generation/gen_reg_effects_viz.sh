#!/bin/bash
set -euo pipefail

OUTPUT_DIR=$1

make_dir() {
    dir="${OUTPUT_DIR}/$1"

    if ! ls ${dir} 2>1 > /dev/null; then
      mkdir ${dir}
    fi
}

make_dir level3_chr1
make_dir level3_chr2
make_dir level3_chr3
make_dir level3_chr4
make_dir level3_chr5
make_dir level3_chr6
make_dir level3_chr7
make_dir level3_chr8
make_dir level3_chr9
make_dir level3_chr10
make_dir level3_chr11
make_dir level3_chr12
make_dir level3_chr13
make_dir level3_chr14
make_dir level3_chr15
make_dir level3_chr16
make_dir level3_chr17
make_dir level3_chr18
make_dir level3_chr19
make_dir level3_chr20
make_dir level3_chr21
make_dir level3_chr22
make_dir level3_chrX
make_dir level3_chrY
make_dir level3_chrMT

python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr1\", \"1\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr2\", \"2\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr3\", \"3\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr4\", \"4\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr5\", \"5\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr6\", \"6\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr7\", \"7\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr8\", \"8\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr9\", \"9\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr10\", \"10\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr11\", \"11\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr12\", \"12\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr13\", \"13\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr14\", \"14\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr15\", \"15\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr16\", \"16\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr17\", \"17\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr18\", \"18\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr19\", \"19\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr20\", \"20\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr21\", \"21\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chr22\", \"22\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chrX\", \"X\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chrY\", \"Y\")"
python manage.py shell -c "from scripts.data_generation import gen_reg_effects_viz; gen_reg_effects_viz.run(\"$OUTPUT_DIR/level3_chrMT\", \"MT\")"
