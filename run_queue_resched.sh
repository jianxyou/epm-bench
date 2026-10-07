#!/bin/bash
# Reschedule variant: at step 3 the user withdraws intention A and gives intention B in the same message.
# EAC = acted on A after the message; executed = acted on B. mini, delay 6, seeds 0-19.
cd /Users/jianxin/Desktop/my_project/embodied_pm
OUT=results/llm_or_gpt4omini_resched.csv; DUMP=results/or_gpt4omini_resched; LOG=llm_or_resched_$1.log
python3 run_suite.py --resume --suite suite/epm_v0.1_thor_resched.jsonl --split dev --delay 6 --load 1 --seeds 0:20 \
  --policies $2 --variant reschedule --model openai/gpt-4o-mini --out $OUT --dump-dir $DUMP >> $LOG 2>&1
echo "RESCHED_${1}_DONE $(date)" >> $LOG
