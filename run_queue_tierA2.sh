#!/bin/bash
# Tier A v2: Llama and Gemini each get a DEDICATED engine (run_tierA.py copy so
# the 2-engine queues don't count them). Global cap 5 engines. Smoke-gated.
cd /Users/jianxin/Desktop/my_project/embodied_pm
SCR=/private/tmp/claude-501/-Users-jianxin-Desktop-my-project/281fe8db-511d-41cc-9e57-a0a441fc7a20/scratchpad
wait_cap() { while [ "$(pgrep -f 'MacOS/Python run_' | wc -l | tr -d ' ')" -ge 5 ]; do sleep 120; done; }
one_model() {
  model=$1; tag=$2
  wait_cap
  python3 run_tierA.py --split dev --delay 6 --load 1 --seeds 0:2 --policies llm:bank --variant live \
    --model "$model" --out $SCR/smoke_$tag.csv > $SCR/smoke_$tag.log 2>&1
  ok=$(python3 -c "import csv;r=list(csv.DictReader(open('$SCR/smoke_$tag.csv')));print(int(sum(int(x['chores_done']) for x in r)>0))" 2>/dev/null || echo 0)
  if [ "$ok" != "1" ]; then echo "SMOKE_FAIL $model $(date)" >> llm_or_tierA.log; return; fi
  echo "SMOKE_OK $model $(date)" >> llm_or_tierA.log
  python3 run_tierA.py --resume --split dev --delay 6 --load 1 --seeds 0:50 --policies llm:bank,llm:sched2,llm:none \
    --variant cancel_early,cancel_late --model "$model" --out results/llm_or_$tag.csv --dump-dir results/or_$tag >> llm_or_tierA.log 2>&1
  wait_cap
  python3 run_tierA.py --resume --split dev --delay 6 --load 1 --seeds 0:50 --policies llm:bank,llm:sched2,llm:none \
    --variant live,control --model "$model" --out results/llm_or_$tag.csv --dump-dir results/or_$tag >> llm_or_tierA.log 2>&1
}
one_model meta-llama/llama-3.3-70b-instruct llama &
sleep 45
one_model google/gemini-2.5-flash-lite gemini &
wait
echo "TIERA_DONE $(date)" >> llm_or_tierA.log
