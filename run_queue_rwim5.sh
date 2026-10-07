#!/bin/bash
# Most valuable run first: rwim5 (self-kept ledger rendered in sched2 wording).
# 1) mini as its own bookkeeper, n=20 x {live, cancel_early, cancel_late}  (~$2)
# 2) if EXEC clearly improves over rwim4, Sonnet-5 bookkeeper, same cells   (~$9, gated on balance)
cd /Users/jianxin/Desktop/my_project/embodied_pm
KEY=$(cat /Users/jianxin/Desktop/my_project/.openrouter_key)
bal() { curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $KEY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['total_credits']-d['total_usage'])"; }
gate() { while python3 -c "import sys; sys.exit(0 if float('$(bal)') < $1 else 1)"; do echo "GATE: balance $(bal) < $1, waiting" >> llm_or_rwim5.log; sleep 1800; done; }

python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:rwim5 \
  --variant live,cancel_early,cancel_late --model openai/gpt-4o-mini \
  --out results/llm_or_gpt4omini.csv --dump-dir results/or_gpt4omini >> llm_or_rwim5.log 2>&1
echo "RWIM5_MINI_DONE $(date)" >> llm_or_rwim5.log

# decide whether the Sonnet run is worth it: EXEC(live) of rwim5 must beat rwim4's 25% clearly
GO=$(python3 - <<'PY'
import csv
rows=[r for r in csv.DictReader(open('results/llm_or_gpt4omini.csv')) if r['policy']=='llm-rwim5' and r['variant']=='live']
ex=sum(r['executed']=='True' for r in rows); print(1 if rows and ex/len(rows) >= 0.45 else 0)
PY
)
if [ "$GO" = "1" ]; then
  gate 7
  python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:20 --policies llm:rwim5 \
    --variant live,cancel_early,cancel_late --model openai/gpt-4o-mini --mem-model anthropic/claude-sonnet-5 \
    --out results/llm_or_gpt4omini.csv --dump-dir results/or_gpt4omini >> llm_or_rwim5.log 2>&1
  echo "RWIM5_SONNET_DONE $(date)" >> llm_or_rwim5.log
else
  echo "RWIM5_SONNET_SKIPPED (mini EXEC < 45%) $(date)" >> llm_or_rwim5.log
fi
