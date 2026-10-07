#!/bin/bash
# Night 5: Sonnet scale check / RGB perception tier / load x sched / top-up.
# Fail-fast on credits happens inside run_pilot; blocks are ||true so one
# transient failure does not kill the chain.
set -x
cd /Users/jianxin/Desktop/my_project/embodied_pm
OUT=results/night5.csv
SONNET=claude-sonnet-5

echo "=== N5-A Sonnet scale check $(date) ==="
for mem in none bank sched rwim; do
  python3 run_pilot.py --policy llm --mem $mem --model $SONNET --episodes 8 --out $OUT || true
  python3 run_pilot.py --policy llm --mem $mem --model $SONNET --episodes 8 --cancel late --out $OUT || true
done
python3 run_pilot.py --policy llm --mem none --model $SONNET --episodes 8 --control --out $OUT || true

echo "=== N5-B RGB perception tier (Haiku) $(date) ==="
for mem in none bank sched; do
  python3 run_pilot.py --policy llm --mem $mem --vision --episodes 8 --out $OUT || true
  python3 run_pilot.py --policy llm --mem $mem --vision --episodes 8 --cancel late --out $OUT || true
done
python3 run_pilot.py --policy llm --mem none --vision --episodes 8 --control --out $OUT || true

echo "=== N5-C intention load x sched (Haiku) $(date) ==="
for n in 1 2 3; do
  python3 run_pilot.py --policy llm --mem sched --load $n --episodes 10 --out $OUT || true
done
python3 run_pilot.py --policy llm --mem bank --load 3 --episodes 10 --out $OUT || true

echo "=== N5-D headline top-up to n=20 (Haiku) $(date) ==="
for mem in none bank sched; do
  python3 run_pilot.py --policy llm --mem $mem --episodes 10 --seed0 10 --out results/llm_real.csv || true
  python3 run_pilot.py --policy llm --mem $mem --episodes 10 --seed0 10 --cancel late --out results/llm_real.csv || true
done
echo "NIGHT5_DONE $(date)"
