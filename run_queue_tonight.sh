#!/bin/bash
# Overnight queue, cheapest-first so a small top-up still buys the useful cells.
cd /Users/jianxin/Desktop/my_project/embodied_pm
PY=$HOME/miniforge3-x86/envs/habitat/bin/python
balance() { python3 -c "
import json,urllib.request
k=open('/Users/jianxin/Desktop/my_project/.openrouter_key').read().strip()
d=json.load(urllib.request.urlopen(urllib.request.Request('https://openrouter.ai/api/v1/credits',headers={'Authorization':f'Bearer {k}'}),timeout=30))['data']
print(d['total_credits']-d['total_usage'])" 2>/dev/null || echo 0; }
gate() { while [ "$(python3 -c "print(int(float('$(balance)') >= $1))")" != "1" ]; do sleep 300; done; }
gate 3
echo "TONIGHT_START balance=$(balance) $(date)" >> llm_or_tonight.log

# 1. Habitat on gpt-4o-mini (~$2): second model in the second simulator
$PY run_suite_habitat.py --resume --split dev --delay 10 --seeds 0:50 --mems bank,sched2 \
   --model openai/gpt-4o-mini --out results/hab_or_gpt4omini.csv --dump-dir results/hab_or_gpt4omini >> hab_or.log 2>&1 &
sleep 30
$PY run_suite_habitat.py --resume --split dev --delay 10 --seeds 0:50 --mems none,sched1 \
   --model openai/gpt-4o-mini --out results/hab_or_gpt4omini_abl.csv --dump-dir results/hab_or_gpt4omini >> hab_or.log 2>&1 &
wait
echo "HAB_MINI_DONE $(date)" >> llm_or_tonight.log

# 2. Habitat held-out scene, Gemini (~$1.5): skokloster-castle, test split
gate 2
$PY run_suite_habitat.py --resume --split test --scene skokloster-castle --delay 10 --seeds 100:130 \
   --mems bank,sched2 --model google/gemini-2.5-flash-lite \
   --out results/hab_or_gemini_test.csv --dump-dir results/hab_or_gemini_test >> hab_or.log 2>&1
echo "HAB_HELDOUT_DONE $(date)" >> llm_or_tonight.log

# 3. THOR delay sweep for the two remaining models (~$3)
gate 4
for M in "deepseek/deepseek-chat deepseek" "meta-llama/llama-3.3-70b-instruct llama"; do
  set -- $M
  for D in 3 10 14; do
    python3 run_suite.py --resume --split dev --delay $D --load 1 --seeds 0:20 \
      --policies llm:bank,llm:sched2 --variant cancel_early,live --model "$1" \
      --out results/llm_or_$2_delay.csv --dump-dir results/or_$2_delay >> llm_or_tonight.log 2>&1
  done
done
echo "DELAY_DONE $(date)" >> llm_or_tonight.log

# 4. Sonnet-5 bookkeeper with the FIXED memory agent (~$7)
gate 12
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:rwim4 \
  --variant cancel_early,cancel_late,live --model openai/gpt-4o-mini \
  --mem-model anthropic/claude-sonnet-5 --out results/llm_or_gpt4omini.csv \
  --dump-dir results/or_gpt4omini >> llm_or_tonight.log 2>&1
echo "TONIGHT_ALL_DONE balance=$(balance) $(date)" >> llm_or_tonight.log
