#!/bin/bash
# Self-kept ledger, fixed (rwim4): memory agent sees entries in full and the
# current observation. mini and Gemini as their own bookkeepers now; the
# Sonnet-5 bookkeeper waits for balance >= $12.
cd /Users/jianxin/Desktop/my_project/embodied_pm
balance() { python3 -c "
import json,urllib.request
k=open('/Users/jianxin/Desktop/my_project/.openrouter_key').read().strip()
d=json.load(urllib.request.urlopen(urllib.request.Request('https://openrouter.ai/api/v1/credits',headers={'Authorization':f'Bearer {k}'}),timeout=30))['data']
print(d['total_credits']-d['total_usage'])" 2>/dev/null || echo 0; }
wait_cap() { while [ "$(pgrep -f 'MacOS/Python run_' | wc -l | tr -d ' ')" -ge 7 ]; do sleep 90; done; }
COMMON="--resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:rwim4"
for M in "google/gemini-2.5-flash-lite gemini" "openai/gpt-4o-mini gpt4omini"; do
  set -- $M; wait_cap
  ( python3 run_suite.py $COMMON --variant cancel_early,cancel_late,live --model "$1" \
      --out results/llm_or_$2.csv --dump-dir results/or_$2 >> llm_or_rwim4.log 2>&1
    python3 run_suite.py $COMMON --variant control --model "$1" \
      --out results/llm_or_$2_ctrl2.csv --dump-dir results/or_$2_ctrl2 >> llm_or_rwim4.log 2>&1 ) &
  sleep 45
done
wait
echo "RWIM4_SELF_DONE $(date)" >> llm_or_rwim4.log
while [ "$(python3 -c "print(int(float('$(balance)') >= 12))")" != "1" ]; do sleep 300; done
python3 run_suite.py $COMMON --variant cancel_early,cancel_late,live --model openai/gpt-4o-mini \
  --mem-model anthropic/claude-sonnet-5 --out results/llm_or_gpt4omini.csv --dump-dir results/or_gpt4omini >> llm_or_rwim4.log 2>&1
echo "RWIM4_SONNET_DONE $(date)" >> llm_or_rwim4.log
