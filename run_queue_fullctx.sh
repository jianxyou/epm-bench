#!/bin/bash
# Full-context control: NONE design with the whole transcript in context (window 40 >= episode length), so the
# briefing and the cancel message never scroll out. Main cell (delay 6, load 1, dev), seeds 0-19, four variants.
# Separate csv/dump because the policy name (llm-none) would collide with the 6-step-window rows.
TAG=$1; M=$2
cd /Users/jianxin/Desktop/my_project/embodied_pm
LOG=llm_or_fullctx_$TAG.log; OUT=results/llm_or_${TAG}_fullctx.csv; DUMP=results/or_${TAG}_fullctx
KEY=$(cat /Users/jianxin/Desktop/my_project/.openrouter_key)
bal() { curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $KEY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['total_credits']-d['total_usage'])"; }
gate() { while python3 -c "import sys; sys.exit(0 if float('$(bal)') < $1 else 1)"; do echo "GATE: balance $(bal) < $1, waiting $(date)" >> $LOG; sleep 900; done; }
COMMON="--resume --split dev --delay 6 --load 1 --seeds 0:20 --window 40 --policies llm:none"
for PASS in 1 2; do
  for V in cancel_early cancel_late live control; do
    gate 1.0
    python3 run_suite.py $COMMON --variant $V --model "$M" --out $OUT --dump-dir $DUMP >> $LOG 2>&1
    echo "PASS$PASS $V done $(date)" >> $LOG
  done
done
echo "FULLCTX_${TAG}_DONE $(date)" >> $LOG
