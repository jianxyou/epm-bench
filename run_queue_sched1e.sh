#!/bin/bash
# Wording ablation, properly matched: sched1e = sched1 wording + task board + every-step injection.
cd /Users/jianxin/Desktop/my_project/embodied_pm
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:sched1e \
  --variant cancel_early,cancel_late --model openai/gpt-4o-mini \
  --out results/llm_or_gpt4omini.csv --dump-dir results/or_gpt4omini >> llm_or_sched1e.log 2>&1
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:sched1e \
  --variant cancel_early,cancel_late --model google/gemini-2.5-flash-lite \
  --out results/llm_or_gemini.csv --dump-dir results/or_gemini >> llm_or_sched1e.log 2>&1
echo "SCHED1E_CANCEL_DONE $(date)" >> llm_or_sched1e.log
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:sched1e \
  --variant live --model openai/gpt-4o-mini --out results/llm_or_gpt4omini.csv --dump-dir results/or_gpt4omini >> llm_or_sched1e.log 2>&1
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:sched1e \
  --variant live --model google/gemini-2.5-flash-lite --out results/llm_or_gemini.csv --dump-dir results/or_gemini >> llm_or_sched1e.log 2>&1
echo "SCHED1E_ALL_DONE $(date)" >> llm_or_sched1e.log
