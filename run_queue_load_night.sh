#!/bin/bash
# Overnight load curve, two parallel queues (A: cancel-early EAC, B: live EXEC). mini actor, delay 6.
# Writes into results/llm_or_gpt4omini_load_v1obs.csv (resume-safe). Balance gate at $2.
cd /Users/jianxin/Desktop/my_project/embodied_pm
Q=$1; OUT=results/llm_or_gpt4omini_load_v1obs.csv; DUMP=results/or_gpt4omini_load_v1obs; LOG=llm_or_load_night_$Q.log
KEY=$(cat /Users/jianxin/Desktop/my_project/.openrouter_key)
bal() { curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $KEY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['total_credits']-d['total_usage'])"; }
gate() { while python3 -c "import sys; sys.exit(0 if float('$(bal)') < $1 else 1)"; do echo "GATE: balance $(bal) < $1, waiting" >> $LOG; sleep 1800; done; }
run() { # $1 suite(or -), $2 load, $3 seeds, $4 policies, $5 variant
  local S=""; [ "$1" != "-" ] && S="--suite $1"
  gate 2
  python3 run_suite.py --resume $S --split dev --delay 6 --load $2 --seeds $3 --policies $4 --variant $5 \
    --model openai/gpt-4o-mini --out $OUT --dump-dir $DUMP >> $LOG 2>&1
  echo "DONE load=$2 seeds=$3 pol=$4 var=$5 $(date)" >> $LOG
}
S4=suite/epm_v0.1_thor_load4.jsonl; S56=suite/epm_v0.1_thor_load56.jsonl; SX=suite/epm_v0.1_thor_load456_s20.jsonl
if [ "$Q" = "A" ]; then
  for L in 2 3; do run - $L 0:20 llm:summ cancel_early; done
  run $S4 4 0:20 llm:summ cancel_early; run $S56 5 0:20 llm:summ cancel_early; run $S56 6 0:20 llm:summ cancel_early
  for L in 2 3; do run - $L 0:20 llm:rwim5 cancel_early; done
  run $S4 4 0:20 llm:rwim5 cancel_early; run $S56 5 0:20 llm:rwim5 cancel_early; run $S56 6 0:20 llm:rwim5 cancel_early
  for L in 1 2 3; do run - $L 20:40 llm:bank,llm:sched2 cancel_early; done
  for L in 4 5 6; do run $SX $L 20:40 llm:bank,llm:sched2 cancel_early; done
  echo "QUEUE_A_DONE $(date)" >> $LOG
else
  for L in 1 2 3; do run - $L 20:40 llm:bank,llm:sched2 live; done
  for L in 4 5 6; do run $SX $L 20:40 llm:bank,llm:sched2 live; done
  for L in 2 3; do run - $L 0:20 llm:summ live; done
  run $S4 4 0:20 llm:summ live; run $S56 5 0:20 llm:summ live; run $S56 6 0:20 llm:summ live
  echo "QUEUE_B_DONE $(date)" >> $LOG
fi
