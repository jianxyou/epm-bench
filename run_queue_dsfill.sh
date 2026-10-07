#!/bin/bash
# DeepSeek gap fill (429s skipped episodes): bank cancel arms first (the naive-
# memory violation number, n=30 -> 50), then none cancel arms, then sched2 gaps.
# New processes pick up the 429/empty-choices retry with long backoff.
cd /Users/jianxin/Desktop/my_project/embodied_pm
wait_cap() { while [ "$(pgrep -f 'MacOS/Python run_' | wc -l | tr -d ' ')" -ge 5 ]; do sleep 120; done; }
M=deepseek/deepseek-chat
for POL in llm:bank llm:none llm:sched2; do
  wait_cap
  python3 run_tierA.py --resume --split dev --delay 6 --load 1 --seeds 0:50 --policies $POL \
    --variant cancel_early,cancel_late --model "$M" --out results/llm_or_deepseek.csv \
    --dump-dir results/or_deepseek >> llm_or_dsfill.log 2>&1
done
echo "DSFILL_DONE $(date)" >> llm_or_dsfill.log
