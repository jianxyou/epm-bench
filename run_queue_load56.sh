#!/bin/bash
# Load curve with v0.1 observation ordering throughout (the earlier load-4 run used v0.2 ordering).
# mini, delay 6, seeds 0-19, cancel-early for bank/sched2/retr2; live for bank/sched2. Separate CSV.
cd /Users/jianxin/Desktop/my_project/embodied_pm
OUT=results/llm_or_gpt4omini_load_v1obs.csv; DUMP=results/or_gpt4omini_load_v1obs
python3 run_suite.py --resume --suite suite/epm_v0.1_thor_load4.jsonl  --split dev --delay 6 --load 4 --seeds 0:20 --policies llm:bank,llm:sched2,llm:retr2 --variant cancel_early --model openai/gpt-4o-mini --out $OUT --dump-dir $DUMP >> llm_or_load56.log 2>&1
python3 run_suite.py --resume --suite suite/epm_v0.1_thor_load56.jsonl --split dev --delay 6 --load 5 --seeds 0:20 --policies llm:bank,llm:sched2,llm:retr2 --variant cancel_early --model openai/gpt-4o-mini --out $OUT --dump-dir $DUMP >> llm_or_load56.log 2>&1
python3 run_suite.py --resume --suite suite/epm_v0.1_thor_load56.jsonl --split dev --delay 6 --load 6 --seeds 0:20 --policies llm:bank,llm:sched2,llm:retr2 --variant cancel_early --model openai/gpt-4o-mini --out $OUT --dump-dir $DUMP >> llm_or_load56.log 2>&1
echo "LOAD456_CANCEL_DONE $(date)" >> llm_or_load56.log
python3 run_suite.py --resume --suite suite/epm_v0.1_thor_load4.jsonl  --split dev --delay 6 --load 4 --seeds 0:20 --policies llm:bank,llm:sched2 --variant live --model openai/gpt-4o-mini --out $OUT --dump-dir $DUMP >> llm_or_load56.log 2>&1
python3 run_suite.py --resume --suite suite/epm_v0.1_thor_load56.jsonl --split dev --delay 6 --load 5 --seeds 0:20 --policies llm:bank,llm:sched2 --variant live --model openai/gpt-4o-mini --out $OUT --dump-dir $DUMP >> llm_or_load56.log 2>&1
python3 run_suite.py --resume --suite suite/epm_v0.1_thor_load56.jsonl --split dev --delay 6 --load 6 --seeds 0:20 --policies llm:bank,llm:sched2 --variant live --model openai/gpt-4o-mini --out $OUT --dump-dir $DUMP >> llm_or_load56.log 2>&1
echo "LOAD456_ALL_DONE $(date)" >> llm_or_load56.log
