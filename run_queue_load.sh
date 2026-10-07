#!/bin/bash
# Load curve: does the rewrite keep working as the number of standing intentions grows?
# mini actor, delay 6, seeds 0-19. Cancel arms for bank/sched2/retr/retr2 at load 4; retr/retr2 at loads 2,3
# (bank/sched2 at loads 2,3 already exist in results/llm_or_gpt4omini_load.csv). Live arms at load 4 for EXEC.
cd /Users/jianxin/Desktop/my_project/embodied_pm
S4=suite/epm_v0.1_thor_load4.jsonl
python3 run_suite.py --resume --suite $S4 --split dev --delay 6 --load 4 --seeds 0:20 --policies llm:bank,llm:sched2,llm:retr2,llm:retr \
  --variant cancel_early,cancel_late --model openai/gpt-4o-mini --out results/llm_or_gpt4omini_load.csv --dump-dir results/or_gpt4omini_load >> llm_or_load.log 2>&1
echo "LOAD4_CANCEL_DONE $(date)" >> llm_or_load.log
python3 run_suite.py --resume --split dev --delay 6 --load 2 --seeds 0:20 --policies llm:retr2,llm:retr \
  --variant cancel_early,cancel_late --model openai/gpt-4o-mini --out results/llm_or_gpt4omini_load.csv --dump-dir results/or_gpt4omini_load >> llm_or_load.log 2>&1
python3 run_suite.py --resume --split dev --delay 6 --load 3 --seeds 0:20 --policies llm:retr2,llm:retr \
  --variant cancel_early,cancel_late --model openai/gpt-4o-mini --out results/llm_or_gpt4omini_load.csv --dump-dir results/or_gpt4omini_load >> llm_or_load.log 2>&1
echo "LOAD23_RETR_DONE $(date)" >> llm_or_load.log
python3 run_suite.py --resume --suite $S4 --split dev --delay 6 --load 4 --seeds 0:20 --policies llm:bank,llm:sched2 \
  --variant live --model openai/gpt-4o-mini --out results/llm_or_gpt4omini_load.csv --dump-dir results/or_gpt4omini_load >> llm_or_load.log 2>&1
echo "LOAD_ALL_DONE $(date)" >> llm_or_load.log
