#!/bin/bash
# RGB tier on a model with real vision: Gemini 2.5 Flash-Lite. Smoke-gated.
cd /Users/jianxin/Desktop/my_project/embodied_pm
SCR=/private/tmp/claude-501/-Users-jianxin-Desktop-my-project/281fe8db-511d-41cc-9e57-a0a441fc7a20/scratchpad
python3 run_sweep.py --split dev --delay 6 --load 1 --seeds 0:2 --policies llm:bank --variant live \
  --model google/gemini-2.5-flash-lite --vision --size 320 --out $SCR/smoke_rgb_gemini.csv > $SCR/smoke_rgb_gemini.log 2>&1
ok=$(python3 -c "import csv;r=list(csv.DictReader(open('$SCR/smoke_rgb_gemini.csv')));print(int(len(r)>0 and sum(int(x['chores_done']) for x in r)>0))" 2>/dev/null || echo 0)
if [ "$ok" != "1" ]; then echo "RGB_GEMINI_SMOKE_FAIL $(date)" >> llm_or_night2.log; exit 0; fi
echo "RGB_GEMINI_SMOKE_OK $(date)" >> llm_or_night2.log
python3 run_sweep.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:bank,llm:sched2 \
  --variant cancel_early,live --model google/gemini-2.5-flash-lite --vision --size 320 \
  --out results/llm_or_gemini_rgb.csv --dump-dir results/or_gemini_rgb >> llm_or_night2.log 2>&1
echo "RGB_GEMINI_DONE $(date)" >> llm_or_night2.log
