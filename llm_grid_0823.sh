#!/bin/bash
# LLM solidification grid (spec §8) — ONE COMMAND once a working API key is in
# /Users/jianxin/Desktop/my_project/.anthropic_key
# (2026-08-23 status: current key returns 401 invalid — needs a NEW key,
#  not a recharge.)
#
# Order: cheapest calibration first, then headline, then extensions. Fail-fast
# on credit exhaustion (agents.py raises FATAL). Everything appends, so
# re-running resumes; arms already at target n are skipped by seed windows.
set -x
cd /Users/jianxin/Desktop/my_project/embodied_pm
export PM_TRACE=1
OUT=results/llm_grid_0823.csv

python3 estimate_llm_cost.py

# 0. calibration: 5 eps/arm to refresh token means (~$2)
for MEM in none bank sched; do
  python3 run_pilot.py --policy llm --mem $MEM --episodes 5 --out $OUT || exit 1
done

# 1. THOR headline: 4 mems x {live,late,early,control} x n=50
for MEM in none bank rwim sched; do
  python3 run_pilot.py --policy llm --mem $MEM --episodes 50 --out $OUT || exit 1
  python3 run_pilot.py --policy llm --mem $MEM --episodes 50 --cancel late --out $OUT || exit 1
  python3 run_pilot.py --policy llm --mem $MEM --episodes 50 --cancel early --out $OUT || exit 1
done
python3 run_pilot.py --policy llm --mem none --episodes 50 --control --out $OUT || exit 1

# 2. load curve
for L in 2 3; do
  for MEM in bank sched; do
    python3 run_pilot.py --policy llm --mem $MEM --load $L --episodes 25 --out $OUT || exit 1
    python3 run_pilot.py --policy llm --mem $MEM --load $L --episodes 25 --cancel late --out $OUT || exit 1
  done
done

# 3. RGB tier
for MEM in bank sched; do
  python3 run_pilot.py --policy llm --mem $MEM --vision --episodes 25 --out $OUT || exit 1
  python3 run_pilot.py --policy llm --mem $MEM --vision --episodes 25 --cancel late --out $OUT || exit 1
done

# 4. Habitat tier (conda env; anthropic must be installed there)
source $HOME/miniforge3-x86/bin/activate && conda activate habitat
for MEM in none bank sched; do
  python pm_habitat.py --policy llm --mem $MEM --real --episodes 50 --out $OUT || exit 1
  python pm_habitat.py --policy llm --mem $MEM --real --episodes 50 --cancel late --out $OUT || exit 1
done

# 5. Sonnet replication
for MEM in none bank sched; do
  python3 run_pilot.py --policy llm --mem $MEM --model claude-sonnet-5 --episodes 25 --out $OUT || exit 1
  python3 run_pilot.py --policy llm --mem $MEM --model claude-sonnet-5 --episodes 25 --cancel late --out $OUT || exit 1
done

echo "LLM_GRID_DONE $(date)"
