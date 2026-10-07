#!/bin/bash
cd /Users/jianxin/Desktop/my_project/embodied_pm
python3 run_tierA.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:sched2 \
  --variant cancel_early,cancel_late --model openai/gpt-5.5 --out results/llm_or_gpt55.csv --dump-dir results/or_gpt55 >> llm_or_frontier.log 2>&1
echo "GPT55_FILL_DONE $(date)" >> llm_or_frontier.log
