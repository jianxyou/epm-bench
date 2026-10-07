#!/bin/bash
# Load curve on a second actor (Gemini 2.5 Flash Lite), loads 4-6, bank + sched2, seeds 0-19, cancel-early then live.
cd /Users/jianxin/Desktop/my_project/embodied_pm
OUT=results/llm_or_gemini_load_v1obs.csv; DUMP=results/or_gemini_load_v1obs; LOG=llm_or_gemini_load456.log; M=google/gemini-2.5-flash-lite
S4=suite/epm_v0.1_thor_load4.jsonl; S56=suite/epm_v0.1_thor_load56.jsonl
for V in cancel_early live; do
  python3 run_suite.py --resume --suite $S4  --split dev --delay 6 --load 4 --seeds 0:20 --policies llm:bank,llm:sched2 --variant $V --model $M --out $OUT --dump-dir $DUMP >> $LOG 2>&1
  python3 run_suite.py --resume --suite $S56 --split dev --delay 6 --load 5 --seeds 0:20 --policies llm:bank,llm:sched2 --variant $V --model $M --out $OUT --dump-dir $DUMP >> $LOG 2>&1
  python3 run_suite.py --resume --suite $S56 --split dev --delay 6 --load 6 --seeds 0:20 --policies llm:bank,llm:sched2 --variant $V --model $M --out $OUT --dump-dir $DUMP >> $LOG 2>&1
  echo "GEMINI_LOAD456_${V}_DONE $(date)" >> $LOG
done
echo "GEMINI_LOAD456_ALL_DONE $(date)" >> $LOG
