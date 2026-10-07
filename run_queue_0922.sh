#!/bin/bash
# 2026-09-22 queue, $15.65. Priority: Sonnet bookkeeper (the one experiment that
# can change the paper) in parallel with Habitat on gpt-4o-mini; then the
# held-out Habitat scene; then delay sweeps only if money is left.
cd /Users/jianxin/Desktop/my_project/embodied_pm
PY=$HOME/miniforge3-x86/envs/habitat/bin/python
balance() { python3 -c "
import json,urllib.request
k=open('/Users/jianxin/Desktop/my_project/.openrouter_key').read().strip()
d=json.load(urllib.request.urlopen(urllib.request.Request('https://openrouter.ai/api/v1/credits',headers={'Authorization':f'Bearer {k}'}),timeout=30))['data']
print(d['total_credits']-d['total_usage'])" 2>/dev/null || echo 0; }
gate() { while [ "$(python3 -c "print(int(float('$(balance)') >= $1))")" != "1" ]; do sleep 300; done; }
echo "Q0922_START balance=$(balance) $(date)" >> llm_or_0922.log

# A. Sonnet-5 bookkeeper, fixed memory agent (rwim4): 60 eps, ~$9
( python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:rwim4 \
    --variant cancel_early,cancel_late,live --model openai/gpt-4o-mini \
    --mem-model anthropic/claude-sonnet-5 --out results/llm_or_gpt4omini.csv \
    --dump-dir results/or_gpt4omini >> llm_or_0922.log 2>&1
  echo "SONNET_RWIM4_DONE $(date)" >> llm_or_0922.log ) &

# B. Habitat on gpt-4o-mini: ~$2.5 (two processes)
( $PY run_suite_habitat.py --resume --split dev --delay 10 --seeds 0:50 --mems bank,sched2 \
     --model openai/gpt-4o-mini --out results/hab_or_gpt4omini.csv --dump-dir results/hab_or_gpt4omini >> hab_or.log 2>&1 &
  sleep 30
  $PY run_suite_habitat.py --resume --split dev --delay 10 --seeds 0:50 --mems none,sched1 \
     --model openai/gpt-4o-mini --out results/hab_or_gpt4omini_abl.csv --dump-dir results/hab_or_gpt4omini >> hab_or.log 2>&1 &
  wait
  echo "HAB_MINI_DONE $(date)" >> llm_or_0922.log
  # C. held-out Habitat scene, Gemini: ~$1.5
  gate 2.5
  $PY run_suite_habitat.py --resume --split test --scene skokloster-castle --delay 10 --seeds 100:130 \
     --mems bank,sched2 --model google/gemini-2.5-flash-lite \
     --out results/hab_or_gemini_test.csv --dump-dir results/hab_or_gemini_test >> hab_or.log 2>&1
  echo "HAB_HELDOUT_DONE $(date)" >> llm_or_0922.log ) &
wait

# D. delay sweeps for DeepSeek and Llama, only with money left (~$3)
gate 3.5
for M in "google/gemini-2.5-flash-lite gemini_skip" "deepseek/deepseek-chat deepseek" "meta-llama/llama-3.3-70b-instruct llama"; do
  set -- $M; [ "$2" = "gemini_skip" ] && continue
  for D in 3 10 14; do
    gate 1
    python3 run_suite.py --resume --split dev --delay $D --load 1 --seeds 0:20 \
      --policies llm:bank,llm:sched2 --variant cancel_early,live --model "$1" \
      --out results/llm_or_$2_delay.csv --dump-dir results/or_$2_delay >> llm_or_0922.log 2>&1
  done
done
echo "Q0922_ALL_DONE balance=$(balance) $(date)" >> llm_or_0922.log
