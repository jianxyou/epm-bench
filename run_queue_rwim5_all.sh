#!/bin/bash
# Self-kept ledger (rwim5, bookkeeper = the actor's own model) on a further actor, seeds 0-49, delay 6, load 1,
# default (v0.1) observation ordering. Cancel/live arms -> main csv, control -> ctrl2 csv. Two passes; balance gate.
TAG=$1; M=$2
cd /Users/jianxin/Desktop/my_project/embodied_pm
LOG=llm_or_rwim5all_$TAG.log
KEY=$(cat /Users/jianxin/Desktop/my_project/.openrouter_key)
bal() { curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $KEY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['total_credits']-d['total_usage'])"; }
gate() { while python3 -c "import sys; sys.exit(0 if float('$(bal)') < $1 else 1)"; do echo "GATE: balance $(bal) < $1, waiting $(date)" >> $LOG; sleep 900; done; }
COMMON="--resume --split dev --delay 6 --load 1 --seeds 0:50"
for PASS in 1 2; do
  for V in cancel_early cancel_late live; do
    gate 1.0
    python3 run_suite.py $COMMON --policies llm:rwim5 --variant $V --model "$M" --out results/llm_or_$TAG.csv --dump-dir results/or_$TAG >> $LOG 2>&1
  done
  gate 1.0
  python3 run_suite.py $COMMON --policies llm:rwim5 --variant control --model "$M" --out results/llm_or_${TAG}_ctrl2.csv --dump-dir results/or_${TAG}_ctrl2 >> $LOG 2>&1
  echo "PASS$PASS done balance=$(bal) $(date)" >> $LOG
done
echo "RWIM5ALL_${TAG}_DONE $(date)" >> $LOG
