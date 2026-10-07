#!/bin/bash
# sched2 (information-matched sched) for mini and DeepSeek.
# cancel arms n=50 first (core claim), then live/control n=50. --resume throughout.
cd /Users/jianxin/Desktop/my_project/embodied_pm
wait_slot() { while [ "$(pgrep -f 'run_suite.py --' | wc -l | tr -d ' ')" -ge 2 ]; do sleep 120; done; }
for VAR in "cancel_early,cancel_late" "live,control"; do
  for M in "openai/gpt-4o-mini gpt4omini" "deepseek/deepseek-chat deepseek"; do
    set -- $M; model=$1; tag=$2
    wait_slot
    python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:50 --policies llm:sched2 \
      --variant $VAR --model "$model" --out results/llm_or_$tag.csv --dump-dir results/or_$tag >> llm_or_sched2.log 2>&1
  done
done
echo "SCHED2_DONE $(date)" >> llm_or_sched2.log
