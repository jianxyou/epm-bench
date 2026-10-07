#!/bin/bash
cd /Users/jianxin/Desktop/my_project/embodied_pm
OUT=results/llm_or_gpt4omini_resched.csv; DUMP=results/or_gpt4omini_resched; LOG=llm_or_resched40.log
python3 run_suite.py --resume --suite suite/epm_v0.1_thor_resched.jsonl --split dev --delay 6 --load 1 --seeds 20:40 \
  --policies llm:bank,llm:sched2,llm:rwim5,llm:summ --variant reschedule --model openai/gpt-4o-mini --out $OUT --dump-dir $DUMP >> $LOG 2>&1
echo "RESCHED40_DONE $(date)" >> $LOG
