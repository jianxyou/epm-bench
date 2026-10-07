#!/bin/bash
# Llama-3.3-70B main table (smoke verified by hand: 12 and 7 puts in 2 eps).
cd /Users/jianxin/Desktop/my_project/embodied_pm
wait_cap() { while [ "$(pgrep -f 'MacOS/Python run_' | wc -l | tr -d ' ')" -ge 5 ]; do sleep 120; done; }
M=meta-llama/llama-3.3-70b-instruct
wait_cap
python3 run_tierA.py --resume --split dev --delay 6 --load 1 --seeds 0:50 --policies llm:bank,llm:sched2,llm:none \
  --variant cancel_early,cancel_late --model "$M" --out results/llm_or_llama.csv --dump-dir results/or_llama >> llm_or_tierA.log 2>&1
wait_cap
python3 run_tierA.py --resume --split dev --delay 6 --load 1 --seeds 0:50 --policies llm:bank,llm:sched2,llm:none \
  --variant live,control --model "$M" --out results/llm_or_llama.csv --dump-dir results/or_llama >> llm_or_tierA.log 2>&1
echo "LLAMA_DONE $(date)" >> llm_or_tierA.log
