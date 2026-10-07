#!/bin/bash
# LLM pilot — run AFTER topping up API credits. Fail-fast on credit errors.
# Total ~60 episodes, Haiku by default (cheap); bump --model for the real run.
set -e
cd "$(dirname "$0")"
M=${1:-claude-haiku-4-5-20251001}

# 1. eviction realized in 3D: window=6, no memory -> briefing dies
python3 run_pilot.py --out results/llm_real.csv --policy llm --mem none --episodes 10 --model "$M"
# 2. always-inject store
python3 run_pilot.py --out results/llm_real.csv --policy llm --mem bank --episodes 10 --model "$M"
# 3. RWIM-style coroutine (note-or-silence)
python3 run_pilot.py --out results/llm_real.csv --policy llm --mem rwim --episodes 10 --model "$M"
# 4. cancellation mirrors for each memory policy
python3 run_pilot.py --out results/llm_real.csv --policy llm --mem none --episodes 10 --cancel late --model "$M"
python3 run_pilot.py --out results/llm_real.csv --policy llm --mem bank --episodes 10 --cancel late --model "$M"
python3 run_pilot.py --out results/llm_real.csv --policy llm --mem rwim --episodes 10 --cancel late --model "$M"
echo LLM_PILOT_DONE
