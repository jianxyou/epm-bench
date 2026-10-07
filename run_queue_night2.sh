#!/bin/bash
# Night 2: (a) rwim3 self-bookkeeping memory, (b) RGB perception tier. mini only.
cd /Users/jianxin/Desktop/my_project/embodied_pm
wait_cap() { while [ "$(pgrep -f 'MacOS/Python run_' | wc -l | tr -d ' ')" -ge 6 ]; do sleep 120; done; }
rwim_branch() {
  wait_cap
  python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:rwim3 \
    --variant cancel_early,cancel_late --model openai/gpt-4o-mini \
    --out results/llm_or_gpt4omini.csv --dump-dir results/or_gpt4omini >> llm_or_night2.log 2>&1
  wait_cap
  python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:rwim3 \
    --variant live,control --model openai/gpt-4o-mini \
    --out results/llm_or_gpt4omini.csv --dump-dir results/or_gpt4omini >> llm_or_night2.log 2>&1
}
rgb_branch() {
  wait_cap
  python3 run_sweep.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:bank,llm:sched2 \
    --variant cancel_early,live --model openai/gpt-4o-mini --vision --size 320 \
    --out results/llm_or_gpt4omini_rgb.csv --dump-dir results/or_gpt4omini_rgb >> llm_or_night2.log 2>&1
}
rgb_branch

echo "NIGHT2_DONE $(date)" >> llm_or_night2.log
