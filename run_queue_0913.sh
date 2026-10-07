#!/bin/bash
# Queue: execution arms to n=50 (both models), then wording ablation.
# Serial on purpose — parallel THOR instances thrash the GPU.
cd /Users/jianxin/Desktop/my_project/embodied_pm
set -x

# 1. mini: live + control to n=50  (the EXEC / MEM column)
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:50 \
  --policies llm:sched,llm:none,llm:bank --variant live,control \
  --model openai/gpt-4o-mini \
  --out results/llm_or_gpt4omini.csv --dump-dir results/or_gpt4omini

# 2. mini: wording ablation to n=50
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:50 \
  --policies llm:sched1 --variant cancel_early,cancel_late \
  --model openai/gpt-4o-mini \
  --out results/llm_or_gpt4omini.csv --dump-dir results/or_gpt4omini

# 3. deepseek: live + control to n=50
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:50 \
  --policies llm:sched,llm:none,llm:bank --variant live,control \
  --model deepseek/deepseek-chat \
  --out results/llm_or_deepseek.csv --dump-dir results/or_deepseek

echo "QUEUE_DONE $(date)"
