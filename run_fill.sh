#!/bin/bash
# Gap-fill: after all queue scripts finish, re-run EVERY segment with --resume
# (idempotent: only missing episodes run). Two engines. Guarantees completeness
# even if a segment was killed by the watchdog or died mid-way.
cd /Users/jianxin/Desktop/my_project/embodied_pm
balance() { python3 -c "
import json,urllib.request
k=open('/Users/jianxin/Desktop/my_project/.openrouter_key').read().strip()
d=json.load(urllib.request.urlopen(urllib.request.Request('https://openrouter.ai/api/v1/credits',headers={'Authorization':f'Bearer {k}'}),timeout=30))['data']
print(d['total_credits']-d['total_usage'])" 2>/dev/null || echo 0; }
# wait for (1) all queue scripts gone and (2) a top-up of at least $8
while pgrep -f 'run_queue_' > /dev/null; do sleep 300; done
while [ "$(python3 -c "print(int(float('$(balance)') >= 8))")" != "1" ]; do sleep 300; done
echo "FILL_START $(date)" >> llm_or_fill.log
wait_slot() { while [ "$(pgrep -f 'MacOS/Python run_s' | wc -l | tr -d ' ')" -ge 2 ]; do sleep 60; done; }
seg() { wait_slot; python3 run_suite.py --resume "$@" >> llm_or_fill.log 2>&1 & sleep 30; }
for M in "openai/gpt-4o-mini gpt4omini" "deepseek/deepseek-chat deepseek" "meta-llama/llama-3.3-70b-instruct llama" "google/gemini-2.5-flash-lite gemini"; do
  set -- $M; model=$1; tag=$2
  seg --split dev --delay 6 --load 1 --seeds 0:50 --policies llm:none,llm:bank,llm:sched2 --variant cancel_early,cancel_late,live,control --model "$model" --out results/llm_or_$tag.csv --dump-dir results/or_$tag
done
seg --split dev --delay 6 --load 1 --seeds 0:50 --policies llm:sched,llm:sched1 --variant cancel_early,cancel_late,live,control --model openai/gpt-4o-mini --out results/llm_or_gpt4omini.csv --dump-dir results/or_gpt4omini
for D in 3 10 14; do
  seg --split dev --delay $D --load 1 --seeds 0:20 --policies llm:bank,llm:sched2 --variant cancel_early,live --model openai/gpt-4o-mini --out results/llm_or_gpt4omini_delay.csv --dump-dir results/or_gpt4omini_delay
done
for SC in FloorPlan2 FloorPlan3 FloorPlan4; do
  seg --split test --scene $SC --seeds 100:120 --policies llm:bank,llm:sched2 --variant cancel_early,live --model openai/gpt-4o-mini --out results/llm_or_gpt4omini_test.csv --dump-dir results/or_gpt4omini_test
done
wait
echo "FILL_DONE $(date)" >> llm_or_fill.log
