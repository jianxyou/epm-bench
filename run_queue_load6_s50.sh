#!/bin/bash
# Six standing intentions brought to 50 seeds: seeds 0-49, four variants, delay 6, FloorPlan1, default (v0.1)
# observation ordering. Suite epm_v0.1_thor_load6_s50.jsonl (identical to every existing load-6 episode).
# --resume skips what is already in the csv. Variants in priority order; two passes; balance gate.
# Several queues may share one csv as long as their policy lists are disjoint and the csv already exists.
TAG=$1; M=$2; POLS=$3; Q=$4
cd /Users/jianxin/Desktop/my_project/embodied_pm
LOG=llm_or_load6s50_${TAG}_$Q.log; OUT=results/llm_or_${TAG}_load_v1obs.csv; DUMP=results/or_${TAG}_load_v1obs
[ -s "$OUT" ] || { echo "missing $OUT, refusing to create it" >> $LOG; exit 1; }
KEY=$(cat /Users/jianxin/Desktop/my_project/.openrouter_key)
bal() { curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $KEY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['total_credits']-d['total_usage'])"; }
gate() { while python3 -c "import sys; sys.exit(0 if float('$(bal)') < $1 else 1)"; do echo "GATE: balance $(bal) < $1, waiting $(date)" >> $LOG; sleep 900; done; }
COMMON="--resume --suite suite/epm_v0.1_thor_load6_s50.jsonl --split dev --delay 6 --load 6 --seeds 0:50"
for PASS in 1 2; do
  for V in cancel_early live cancel_late control; do
    for POL in $POLS; do
      gate 1.0
      python3 run_suite.py $COMMON --policies $POL --variant $V --model "$M" --out $OUT --dump-dir $DUMP >> $LOG 2>&1
      echo "PASS$PASS $POL $V done $(date)" >> $LOG
    done
  done
done
echo "LOAD6S50_${TAG}_${Q}_DONE $(date)" >> $LOG
