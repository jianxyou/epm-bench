#!/bin/bash
# Remaining THOR runs, started in parallel instead of waiting behind the slow
# DeepSeek control run. Everything uses --resume.
cd /Users/jianxin/Desktop/my_project/embodied_pm
wait_cap() { while [ "$(pgrep -f 'MacOS/Python run_' | wc -l | tr -d ' ')" -ge 6 ]; do sleep 90; done; }
COMMON="--resume --split dev --delay 6 --load 1"
# A. load sweep on gpt-4o-mini (two engines)
bash run_queue_load.sh openai/gpt-4o-mini gpt4omini &
sleep 60
# B/C. retr2 on both models: cancel arms + live, then exposure-matched control
for M in "openai/gpt-4o-mini gpt4omini" "google/gemini-2.5-flash-lite gemini"; do
  set -- $M; wait_cap
  ( python3 run_suite.py $COMMON --seeds 0:20 --policies llm:retr2 --variant cancel_early,cancel_late,live \
      --model "$1" --out results/llm_or_$2.csv --dump-dir results/or_$2 >> llm_or_topup.log 2>&1
    python3 run_suite.py $COMMON --seeds 0:20 --policies llm:retr2 --variant control \
      --model "$1" --out results/llm_or_$2_ctrl2.csv --dump-dir results/or_$2_ctrl2 >> llm_or_topup.log 2>&1 ) &
  sleep 45
done
# D. exposure-matched control for the other regimes
for M in "openai/gpt-4o-mini gpt4omini" "google/gemini-2.5-flash-lite gemini"; do
  set -- $M; wait_cap
  python3 run_suite.py $COMMON --seeds 0:20 --policies llm:retr,llm:summ,llm:rwim3 --variant control \
    --model "$1" --out results/llm_or_$2_ctrl2.csv --dump-dir results/or_$2_ctrl2 >> llm_or_topup.log 2>&1 &
  sleep 45
done
wait
# make sure the DeepSeek control cell is complete (in case its process died)
python3 run_suite.py $COMMON --seeds 0:50 --policies llm:bank,llm:sched2 --variant control \
  --model deepseek/deepseek-chat --out results/llm_or_deepseek_ctrl2.csv --dump-dir results/or_deepseek_ctrl2 >> llm_or_topup.log 2>&1
echo "TOPUP_CORE_DONE $(date)" >> llm_or_topup.log
