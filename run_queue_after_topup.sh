#!/bin/bash
# Everything that is waiting for credit, in priority order. Starts by itself
# once the balance reaches $10; the frontier block waits for $45.
cd /Users/jianxin/Desktop/my_project/embodied_pm
balance() { python3 -c "
import json,urllib.request
k=open('/Users/jianxin/Desktop/my_project/.openrouter_key').read().strip()
d=json.load(urllib.request.urlopen(urllib.request.Request('https://openrouter.ai/api/v1/credits',headers={'Authorization':f'Bearer {k}'}),timeout=30))['data']
print(d['total_credits']-d['total_usage'])" 2>/dev/null || echo 0; }
gate() { while [ "$(python3 -c "print(int(float('$(balance)') >= $1))")" != "1" ]; do sleep 300; done; }
wait_cap() { while [ "$(pgrep -f 'MacOS/Python run_' | wc -l | tr -d ' ')" -ge 5 ]; do sleep 90; done; }
COMMON="--resume --split dev --delay 6 --load 1"
gate 10
echo "TOPUP_QUEUE_START balance=$(balance) $(date)" >> llm_or_topup.log

# 1. exposure-matched control twins (fix of 2026-09-20) -> *_ctrl2.csv
for M in "openai/gpt-4o-mini gpt4omini" "google/gemini-2.5-flash-lite gemini" "meta-llama/llama-3.3-70b-instruct llama" "deepseek/deepseek-chat deepseek"; do
  set -- $M; wait_cap
  python3 run_suite.py $COMMON --seeds 0:50 --policies llm:bank,llm:sched2 --variant control \
    --model "$1" --out results/llm_or_$2_ctrl2.csv --dump-dir results/or_$2_ctrl2 >> llm_or_topup.log 2>&1 &
  sleep 40
done
wait
for M in "openai/gpt-4o-mini gpt4omini" "google/gemini-2.5-flash-lite gemini"; do
  set -- $M; wait_cap
  python3 run_suite.py $COMMON --seeds 0:20 --policies llm:retr,llm:summ,llm:rwim3 --variant control \
    --model "$1" --out results/llm_or_$2_ctrl2.csv --dump-dir results/or_$2_ctrl2 >> llm_or_topup.log 2>&1 &
  sleep 40
done
wait

# 2. load sweep on gpt-4o-mini (two engines inside)
bash run_queue_load.sh openai/gpt-4o-mini gpt4omini

# 3. retr2: status-tracked entry delivered by retrieval, not always injected
for M in "openai/gpt-4o-mini gpt4omini" "google/gemini-2.5-flash-lite gemini"; do
  set -- $M; wait_cap
  ( python3 run_suite.py $COMMON --seeds 0:20 --policies llm:retr2 --variant cancel_early,cancel_late,live \
      --model "$1" --out results/llm_or_$2.csv --dump-dir results/or_$2 >> llm_or_topup.log 2>&1
    python3 run_suite.py $COMMON --seeds 0:20 --policies llm:retr2 --variant control \
      --model "$1" --out results/llm_or_$2_ctrl2.csv --dump-dir results/or_$2_ctrl2 >> llm_or_topup.log 2>&1 ) &
  sleep 40
done
wait
echo "TOPUP_CORE_DONE balance=$(balance) $(date)" >> llm_or_topup.log

# 4. frontier models: live arm + control (fills the EXEC / floor columns)
gate 45
for M in "anthropic/claude-sonnet-5 sonnet5" "openai/gpt-5.5 gpt55"; do
  set -- $M; wait_cap
  python3 run_suite.py $COMMON --seeds 0:20 --policies llm:bank,llm:sched2 --variant live \
    --model "$1" --out results/llm_or_$2.csv --dump-dir results/or_$2 >> llm_or_topup.log 2>&1
  python3 run_suite.py $COMMON --seeds 0:20 --policies llm:bank,llm:sched2 --variant control \
    --model "$1" --out results/llm_or_$2_ctrl2.csv --dump-dir results/or_$2_ctrl2 >> llm_or_topup.log 2>&1
done
echo "TOPUP_ALL_DONE balance=$(balance) $(date)" >> llm_or_topup.log
