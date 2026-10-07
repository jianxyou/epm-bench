#!/bin/bash
# Night 3 (budget ~$4.3): replicate robustness sweeps + wording ablation + rwim3
# on Gemini-2.5-Flash-Lite so the robustness section is two-model.
cd /Users/jianxin/Desktop/my_project/embodied_pm
G=google/gemini-2.5-flash-lite
wait_cap() { while [ "$(pgrep -f 'MacOS/Python run_' | wc -l | tr -d ' ')" -ge 4 ]; do sleep 120; done; }
branch_a() {
  wait_cap
  python3 run_tierA.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:sched1,llm:rwim3 \
    --variant cancel_early,cancel_late --model $G --out results/llm_or_gemini.csv --dump-dir results/or_gemini >> llm_or_night3.log 2>&1
  wait_cap
  python3 run_tierA.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:rwim3 \
    --variant live,control --model $G --out results/llm_or_gemini.csv --dump-dir results/or_gemini >> llm_or_night3.log 2>&1
}
branch_b() {
  for D in 3 10 14; do
    wait_cap
    python3 run_sweep.py --resume --split dev --delay $D --load 1 --seeds 0:20 --policies llm:bank,llm:sched2 \
      --variant cancel_early,live --model $G --out results/llm_or_gemini_delay.csv --dump-dir results/or_gemini_delay >> llm_or_night3.log 2>&1
  done
  for SC in FloorPlan2 FloorPlan3 FloorPlan4; do
    wait_cap
    python3 run_sweep.py --resume --split test --scene $SC --seeds 100:120 --policies llm:bank,llm:sched2 \
      --variant cancel_early,live --model $G --out results/llm_or_gemini_test.csv --dump-dir results/or_gemini_test >> llm_or_night3.log 2>&1
  done
}
branch_a &
sleep 45
branch_b &
wait
echo "NIGHT3_DONE $(date)" >> llm_or_night3.log
