#!/bin/bash
# Six standing intentions, same four variants and six designs as the main table. seeds 0-19, delay 6, FloorPlan1,
# default (v0.1) observation ordering. Variants in priority order (cancel_early, live first). Two passes; balance gate.
TAG=$1; M=$2; POLS=$3; Q=$4
cd /Users/jianxin/Desktop/my_project/embodied_pm
LOG=llm_or_load6tab_${TAG}_$Q.log; OUT=results/llm_or_${TAG}_load_v1obs.csv; DUMP=results/or_${TAG}_load_v1obs
KEY=$(cat /Users/jianxin/Desktop/my_project/.openrouter_key)
bal() { curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $KEY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['total_credits']-d['total_usage'])"; }
gate() { while python3 -c "import sys; sys.exit(0 if float('$(bal)') < $1 else 1)"; do echo "GATE: balance $(bal) < $1, waiting $(date)" >> $LOG; sleep 900; done; }
COMMON="--resume --suite suite/epm_v0.1_thor_load6_full.jsonl --split dev --delay 6 --load 6 --seeds 0:20"
for PASS in 1 2; do
  for V in cancel_early live cancel_late control; do
    for POL in $POLS; do
      gate 1.0
      python3 run_suite.py $COMMON --policies $POL --variant $V --model "$M" --out $OUT --dump-dir $DUMP >> $LOG 2>&1
      echo "PASS$PASS $POL $V done $(date)" >> $LOG
    done
  done
done
echo "LOAD6TAB_${TAG}_${Q}_DONE $(date)" >> $LOG
