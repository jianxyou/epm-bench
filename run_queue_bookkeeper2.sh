#!/bin/bash
# Sonnet-5 bookkeeper, trimmed to protect the higher-priority runs' budget:
# cancel arms (already running) then LIVE only. No control cell (saves ~$2.5).
cd /Users/jianxin/Desktop/my_project/embodied_pm
while pgrep -f 'mem-model anthropic/claude-sonnet-5' > /dev/null; do sleep 60; done
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:rwim3 \
  --variant live --model openai/gpt-4o-mini --mem-model anthropic/claude-sonnet-5 \
  --out results/llm_or_gpt4omini.csv --dump-dir results/or_gpt4omini >> llm_or_bookkeeper.log 2>&1
echo "BOOKKEEPER_DONE $(date)" >> llm_or_bookkeeper.log
