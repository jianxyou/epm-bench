#!/bin/bash
# 1) rwim5 with Gemini as actor (second actor for the self-kept ledger), n=20 x 3 arms  (~$1.5)
cd /Users/jianxin/Desktop/my_project/embodied_pm
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:rwim5 \
  --variant live,cancel_early,cancel_late --model google/gemini-2.5-flash-lite \
  --out results/llm_or_gemini.csv --dump-dir results/or_gemini >> llm_or_0924.log 2>&1
echo "GEMINI_RWIM5_DONE $(date)" >> llm_or_0924.log

# 2) ask-vs-act probe: bank, mini, cancel_early n=20; each step the actor is also asked
#    (in a side call, same context) whether the instruction is still in force  (~$1)
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:bank \
  --variant cancel_early --model openai/gpt-4o-mini --probe \
  --out results/llm_or_gpt4omini_probe.csv --dump-dir results/or_gpt4omini_probe >> llm_or_0924.log 2>&1
echo "PROBE_DONE $(date)" >> llm_or_0924.log
