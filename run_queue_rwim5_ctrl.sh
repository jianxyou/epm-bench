#!/bin/bash
cd /Users/jianxin/Desktop/my_project/embodied_pm
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:rwim5 --variant control \
  --model openai/gpt-4o-mini --out results/llm_or_gpt4omini_ctrl2.csv --dump-dir results/or_gpt4omini_ctrl2 >> llm_or_rwim5_ctrl.log 2>&1
echo "RWIM5_CTRL_DONE $(date)" >> llm_or_rwim5_ctrl.log
