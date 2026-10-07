#!/bin/bash
# Held-out kitchens (test split seeds are 100..199, not 0..99).
cd /Users/jianxin/Desktop/my_project/embodied_pm
wait_cap() { while [ "$(pgrep -f 'MacOS/Python run_' | wc -l | tr -d ' ')" -ge 5 ]; do sleep 120; done; }
for SC in FloorPlan2 FloorPlan3 FloorPlan4; do
  wait_cap
  python3 run_sweep.py --resume --split test --scene $SC --seeds 100:120 \
    --policies llm:bank,llm:sched2 --variant cancel_early,live \
    --model openai/gpt-4o-mini --out results/llm_or_gpt4omini_test.csv \
    --dump-dir results/or_gpt4omini_test >> llm_or_tierC.log 2>&1
done
echo "TIERC2_DONE $(date)" >> llm_or_tierC.log
