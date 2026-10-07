#!/bin/bash
# Bring RETR and SUMM (and, for gpt4omini, the mini-kept ledger rwim5) from 20 to 50 seeds: seeds 20-49,
# delay 6, load 1, dev split, default (v0.1) observation ordering. Cancel/live arms -> main csv, control -> ctrl2 csv.
# Small chunks with a balance gate before each; the whole list runs twice so that any episode skipped by a
# transient API error in pass 1 is filled in pass 2 (--resume skips what is already there).
TAG=$1; M=$2; POLS=$3
cd /Users/jianxin/Desktop/my_project/embodied_pm
LOG=llm_or_seed50_$TAG.log
KEY=$(cat /Users/jianxin/Desktop/my_project/.openrouter_key)
bal() { curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $KEY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['total_credits']-d['total_usage'])"; }
gate() { while python3 -c "import sys; sys.exit(0 if float('$(bal)') < $1 else 1)"; do echo "GATE: balance $(bal) < $1, waiting $(date)" >> $LOG; sleep 900; done; }
COMMON="--resume --split dev --delay 6 --load 1 --seeds 20:50"
for PASS in 1 2; do
  for POL in $POLS; do
    for V in cancel_early cancel_late live; do
      gate 1.0
      python3 run_suite.py $COMMON --policies $POL --variant $V --model "$M" --out results/llm_or_$TAG.csv --dump-dir results/or_$TAG >> $LOG 2>&1
    done
    gate 1.0
    python3 run_suite.py $COMMON --policies $POL --variant control --model "$M" --out results/llm_or_${TAG}_ctrl2.csv --dump-dir results/or_${TAG}_ctrl2 >> $LOG 2>&1
    echo "PASS$PASS $POL done balance=$(bal) $(date)" >> $LOG
  done
done
echo "SEED50_${TAG}_DONE $(date)" >> $LOG
