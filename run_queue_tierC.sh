#!/bin/bash
# Tier C (robustness sweeps), mini, bank vs sched2, n=20 per cell.
# Runs as the THIRD engine: uses run_sweep.py (a copy of run_suite.py) so the
# 2-engine queues' pgrep pattern 'run_suite.py --' does not count it, while
# this script itself caps total engines at 3.
cd /Users/jianxin/Desktop/my_project/embodied_pm
wait_slot() { while [ "$(pgrep -f 'MacOS/Python run_s' | wc -l | tr -d ' ')" -ge 3 ]; do sleep 120; done; }
# (a) delay sweep on dev: delays 3/10/14 (6 already at n=50)
for D in 3 10 14; do
  wait_slot
  python3 run_sweep.py --resume --split dev --delay $D --load 1 --seeds 0:20 \
    --policies llm:bank,llm:sched2 --variant cancel_early,live \
    --model openai/gpt-4o-mini --out results/llm_or_gpt4omini_delay.csv \
    --dump-dir results/or_gpt4omini_delay >> llm_or_tierC.log 2>&1
done
# (b) held-out kitchens: test split FloorPlan2/3/4 (delay 6, load 1)
for SC in FloorPlan2 FloorPlan3 FloorPlan4; do
  wait_slot
  python3 run_sweep.py --resume --split test --scene $SC --seeds 0:20 \
    --policies llm:bank,llm:sched2 --variant cancel_early,live \
    --model openai/gpt-4o-mini --out results/llm_or_gpt4omini_test.csv \
    --dump-dir results/or_gpt4omini_test >> llm_or_tierC.log 2>&1
done
echo "TIERC_DONE $(date)" >> llm_or_tierC.log
