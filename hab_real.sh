#!/bin/bash
set -x
cd /Users/jianxin/Desktop/my_project/embodied_pm
source $HOME/miniforge3-x86/bin/activate
conda activate habitat
OUT=results/hab_real.csv
for mem in none bank sched; do
  python pm_habitat.py --policy llm --mem $mem --real --episodes 10 --out $OUT || true
  python pm_habitat.py --policy llm --mem $mem --real --episodes 10 --cancel late --out $OUT || true
done
echo HAB_REAL_DONE $(date)
