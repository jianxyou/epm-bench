#!/bin/bash
# "Does a better bookkeeper fix it?" — self-kept ledger (rwim3) with Claude
# Sonnet 5 as the memory agent and GPT-4o-mini as the actor. n=20 per variant.
# Memory agent: ~1 call/step x 40 steps x ~1.5k tok ~= $0.07/ep -> ~$6 total.
cd /Users/jianxin/Desktop/my_project/embodied_pm
balance() { python3 -c "
import json,urllib.request
k=open('/Users/jianxin/Desktop/my_project/.openrouter_key').read().strip()
d=json.load(urllib.request.urlopen(urllib.request.Request('https://openrouter.ai/api/v1/credits',headers={'Authorization':f'Bearer {k}'}),timeout=30))['data']
print(d['total_credits']-d['total_usage'])" 2>/dev/null || echo 0; }
# wait for a top-up: this run needs ~$6 on top of the baselines still running
while [ "$(python3 -c "print(int(float('$(balance)') >= 12))")" != "1" ]; do sleep 300; done
echo "BOOKKEEPER_START balance=$(balance) $(date)" >> llm_or_bookkeeper.log
wait_cap() { while [ "$(pgrep -f 'MacOS/Python run_' | wc -l | tr -d ' ')" -ge 4 ]; do sleep 120; done; }
wait_cap
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:rwim3 \
  --variant cancel_early,cancel_late --model openai/gpt-4o-mini --mem-model anthropic/claude-sonnet-5 \
  --out results/llm_or_gpt4omini.csv --dump-dir results/or_gpt4omini >> llm_or_bookkeeper.log 2>&1
wait_cap
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:rwim3 \
  --variant live,control --model openai/gpt-4o-mini --mem-model anthropic/claude-sonnet-5 \
  --out results/llm_or_gpt4omini.csv --dump-dir results/or_gpt4omini >> llm_or_bookkeeper.log 2>&1
echo "BOOKKEEPER_DONE $(date)" >> llm_or_bookkeeper.log
