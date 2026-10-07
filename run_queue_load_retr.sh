#!/bin/bash
cd /Users/jianxin/Desktop/my_project/embodied_pm
OUT=results/llm_or_gpt4omini_load_v1obs.csv; DUMP=results/or_gpt4omini_load_v1obs
python3 run_suite.py --resume --suite suite/epm_v0.1_thor_load4.jsonl  --split dev --delay 6 --load 4 --seeds 0:20 --policies llm:retr --variant cancel_early --model openai/gpt-4o-mini --out $OUT --dump-dir $DUMP >> llm_or_load56.log 2>&1
python3 run_suite.py --resume --suite suite/epm_v0.1_thor_load56.jsonl --split dev --delay 6 --load 5 --seeds 0:20 --policies llm:retr --variant cancel_early --model openai/gpt-4o-mini --out $OUT --dump-dir $DUMP >> llm_or_load56.log 2>&1
python3 run_suite.py --resume --suite suite/epm_v0.1_thor_load56.jsonl --split dev --delay 6 --load 6 --seeds 0:20 --policies llm:retr --variant cancel_early --model openai/gpt-4o-mini --out $OUT --dump-dir $DUMP >> llm_or_load56.log 2>&1
echo "LOAD456_RETR_DONE $(date)" >> llm_or_load56.log
