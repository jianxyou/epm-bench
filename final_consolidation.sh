#!/bin/bash
set -x
cd "$(dirname "$0")"
# THOR side (system python)
OUT=results/final_bigN.csv
for mem in none bank rwim; do
  python3 run_pilot.py --policy mock --mem $mem --episodes 76 --seed0 100 --out $OUT || true
  python3 run_pilot.py --policy mock --mem $mem --episodes 76 --seed0 100 --cancel late --out $OUT || true
done
for w in 3 12 24 48; do
  python3 run_pilot.py --policy mock --mem none --window $w --episodes 24 --seed0 200 --out $OUT || true
done
python3 run_pilot.py --policy adaptive --k 8 --episodes 48 --seed0 300 --out $OUT || true
python3 run_pilot.py --policy patroller --k 8 --episodes 48 --seed0 300 --out $OUT || true
# Habitat side
source $HOME/miniforge3-x86/bin/activate && conda activate habitat
OUT2=results/final_bigN_hab.csv
for mem in none bank rwim; do
  python pm_habitat.py --policy llm --mem $mem --episodes 76 --seed0 100 --out $OUT2 || true
  python pm_habitat.py --policy llm --mem $mem --episodes 76 --seed0 100 --cancel late --out $OUT2 || true
done
echo FINAL_DONE $(date)
