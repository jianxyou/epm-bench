#!/bin/bash
cd /Users/jianxin/Desktop/my_project/embodied_pm
for i in $(seq 1 30); do
  if python3 -c "
import anthropic
key=open('/Users/jianxin/Desktop/my_project/.anthropic_key').read().strip()
c=anthropic.Anthropic(api_key=key)
c.messages.create(model='claude-haiku-4-5-20251001',max_tokens=1,messages=[{'role':'user','content':'hi'}])
" 2>/dev/null; then
    echo "CREDITS LIVE at probe $i, $(date)"
    echo "=== smoke 2 eps ==="
    python3 run_pilot.py --policy llm --mem none --episodes 2 --out results/llm_smoke.csv || exit 1
    echo "=== full pilot ==="
    bash llm_pilot.sh
    echo "LLM_ALL_DONE $(date)"
    exit 0
  fi
  echo "probe $i: not yet, $(date)"
  sleep 60
done
echo "GAVE_UP after 30 min"
