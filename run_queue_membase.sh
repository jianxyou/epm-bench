#!/bin/bash
# Real memory-system baselines: retrieval (retr) and rolling summary (summ).
# mini first (cancel arms, then live/control), then Gemini. n=20 per variant.
cd /Users/jianxin/Desktop/my_project/embodied_pm
wait_cap() { while [ "$(pgrep -f 'MacOS/Python run_' | wc -l | tr -d ' ')" -ge 4 ]; do sleep 120; done; }
for M in "openai/gpt-4o-mini gpt4omini" "google/gemini-2.5-flash-lite gemini"; do
  set -- $M
  wait_cap
  python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:retr,llm:summ \
    --variant cancel_early,cancel_late --model "$1" --out results/llm_or_$2.csv --dump-dir results/or_$2 >> llm_or_membase.log 2>&1
  wait_cap
  python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:retr,llm:summ \
    --variant live,control --model "$1" --out results/llm_or_$2.csv --dump-dir results/or_$2 >> llm_or_membase.log 2>&1
done
echo "MEMBASE_DONE $(date)" >> llm_or_membase.log
