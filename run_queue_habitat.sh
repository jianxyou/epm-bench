#!/bin/bash
# Habitat LLM tier on the frozen suite (dev, apartment_1, delay 10, seeds 0:50,
# four twins). Two processes per model, separate CSVs to avoid header races:
#   hab_or_<tag>.csv      bank, sched2   (the core contrast)
#   hab_or_<tag>_abl.csv  none, sched1   (floor + wording ablation)
# Gemini starts now; gpt-4o-mini waits until the THOR core queue is done and
# at least $3 is left.
cd /Users/jianxin/Desktop/my_project/embodied_pm
PY=$HOME/miniforge3-x86/envs/habitat/bin/python
balance() { python3 -c "
import json,urllib.request
k=open('/Users/jianxin/Desktop/my_project/.openrouter_key').read().strip()
d=json.load(urllib.request.urlopen(urllib.request.Request('https://openrouter.ai/api/v1/credits',headers={'Authorization':f'Bearer {k}'}),timeout=30))['data']
print(d['total_credits']-d['total_usage'])" 2>/dev/null || echo 0; }
one_model() {
  model=$1; tag=$2
  $PY run_suite_habitat.py --resume --split dev --delay 10 --seeds 0:50 --mems bank,sched2 \
     --model "$model" --out results/hab_or_$tag.csv --dump-dir results/hab_or_$tag >> hab_or.log 2>&1 &
  sleep 30
  $PY run_suite_habitat.py --resume --split dev --delay 10 --seeds 0:50 --mems none,sched1 \
     --model "$model" --out results/hab_or_${tag}_abl.csv --dump-dir results/hab_or_$tag >> hab_or.log 2>&1 &
  wait
  echo "HAB_DONE $tag $(date)" >> hab_or.log
}
one_model google/gemini-2.5-flash-lite gemini
while ! grep -q "TOPUP_CORE_DONE" llm_or_topup.log 2>/dev/null; do sleep 300; done
while [ "$(python3 -c "print(int(float('$(balance)') >= 3))")" != "1" ]; do sleep 300; done
one_model openai/gpt-4o-mini gpt4omini
echo "HAB_ALL_DONE $(date)" >> hab_or.log
