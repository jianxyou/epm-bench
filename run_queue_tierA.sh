#!/bin/bash
# Tier A: main table for model families 3 and 4 (Meta, Google).
# Waits for a free engine slot (<2 run_suite processes), smoke-tests 2 eps,
# aborts the model if the agent does zero chores (parse failure), else runs
# cancel arms n=50 first, then live/control n=50. All with --resume.
cd /Users/jianxin/Desktop/my_project/embodied_pm
SCR=/private/tmp/claude-501/-Users-jianxin-Desktop-my-project/281fe8db-511d-41cc-9e57-a0a441fc7a20/scratchpad
wait_slot() { while [ "$(pgrep -f 'run_suite.py --' | wc -l | tr -d ' ')" -ge 2 ]; do sleep 120; done; }
for M in "meta-llama/llama-3.3-70b-instruct llama" "google/gemini-2.5-flash-lite gemini"; do
  set -- $M; model=$1; tag=$2
  wait_slot
  python3 run_suite.py --split dev --delay 6 --load 1 --seeds 0:2 --policies llm:bank --variant live \
    --model $model --out $SCR/smoke_$tag.csv > $SCR/smoke_$tag.log 2>&1
  ok=$(python3 -c "import csv;r=list(csv.DictReader(open('$SCR/smoke_$tag.csv')));print(int(sum(int(x['chores_done']) for x in r)>0))" 2>/dev/null || echo 0)
  if [ "$ok" != "1" ]; then echo "SMOKE_FAIL $model $(date)" >> llm_or_tierA.log; continue; fi
  echo "SMOKE_OK $model $(date)" >> llm_or_tierA.log
  python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:50 --policies llm:bank,llm:sched2,llm:none \
    --variant cancel_early,cancel_late --model $model --out results/llm_or_$tag.csv --dump-dir results/or_$tag >> llm_or_tierA.log 2>&1
  wait_slot
  python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:50 --policies llm:bank,llm:sched2,llm:none \
    --variant live,control --model $model --out results/llm_or_$tag.csv --dump-dir results/or_$tag >> llm_or_tierA.log 2>&1
done
echo "TIERA_DONE $(date)" >> llm_or_tierA.log
