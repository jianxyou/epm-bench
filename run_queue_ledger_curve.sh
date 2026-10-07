#!/bin/bash
# Load curve for the self-kept ledger (rwim5), loads 2-5, seeds 0-19, cancel-early then live, default (v0.1)
# observation ordering. Fills what the load figure needs: both variants for Gemini, the live variant for GPT-4o-mini
# (its cancel-early cells exist and are skipped by --resume). Same suites and seeds as the BANK/SCHED load curve.
TAG=$1; M=$2
cd /Users/jianxin/Desktop/my_project/embodied_pm
LOG=llm_or_ledgercurve_$TAG.log; OUT=results/llm_or_${TAG}_load_v1obs.csv; DUMP=results/or_${TAG}_load_v1obs
[ -s "$OUT" ] || { echo "missing $OUT, refusing to create it" >> $LOG; exit 1; }
KEY=$(cat /Users/jianxin/Desktop/my_project/.openrouter_key)
bal() { curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $KEY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['total_credits']-d['total_usage'])"; }
gate() { while python3 -c "import sys; sys.exit(0 if float('$(bal)') < $1 else 1)"; do echo "GATE: balance $(bal) < $1, waiting $(date)" >> $LOG; sleep 900; done; }
S4=suite/epm_v0.1_thor_load4.jsonl; S56=suite/epm_v0.1_thor_load56.jsonl
run() { local S=""; [ "$1" != "-" ] && S="--suite $1"; gate 1.0
  python3 run_suite.py --resume $S --split dev --delay 6 --load $2 --seeds 0:20 --policies llm:rwim5 --variant $3 --model "$M" --out $OUT --dump-dir $DUMP >> $LOG 2>&1; }
for PASS in 1 2; do
  for V in cancel_early live; do
    run - 2 $V; run - 3 $V; run $S4 4 $V; run $S56 5 $V
    echo "PASS$PASS $V done $(date)" >> $LOG
  done
done
echo "LEDGERCURVE_${TAG}_DONE $(date)" >> $LOG
