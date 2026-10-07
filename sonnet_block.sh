#!/bin/bash
set -x
cd /Users/jianxin/Desktop/my_project/embodied_pm
OUT=results/sonnet.csv
M=claude-sonnet-5
for mem in none bank sched rwim; do
  python3 run_pilot.py --policy llm --mem $mem --model $M --episodes 8 --out $OUT || true
  python3 run_pilot.py --policy llm --mem $mem --model $M --episodes 8 --cancel late --out $OUT || true
done
python3 run_pilot.py --policy llm --mem none --model $M --episodes 8 --control --out $OUT || true
echo SONNET_DONE $(date)
