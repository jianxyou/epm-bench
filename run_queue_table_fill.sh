#!/bin/bash
# Fill the main table (Table 2).
#   mode "cheap TAG MODEL": RETR + SUMM for a mid-sized actor (live/cancel arms -> main csv, control -> ctrl2 csv)
#   mode "frontier": floors (bank control) for Sonnet 5 and GPT-5.5 once balance >= 12; then sched2 control + live arms once balance >= 30
cd /Users/jianxin/Desktop/my_project/embodied_pm
KEY=$(cat /Users/jianxin/Desktop/my_project/.openrouter_key)
bal() { curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $KEY" | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['total_credits']-d['total_usage'])"; }
gate() { while python3 -c "import sys; sys.exit(0 if float('$(bal)') < $1 else 1)"; do echo "GATE: balance $(bal) < $1, waiting $(date)" >> $LOG; sleep 900; done; }
COMMON="--resume --split dev --delay 6 --load 1 --seeds 0:20"
if [ "$1" = "cheap" ]; then
  TAG=$2; M=$3; LOG=llm_or_tablefill_$TAG.log
  gate 1.5
  python3 run_suite.py $COMMON --policies llm:retr,llm:summ --variant cancel_early,cancel_late,live --model "$M" --out results/llm_or_$TAG.csv --dump-dir results/or_$TAG >> $LOG 2>&1
  gate 1.5
  python3 run_suite.py $COMMON --policies llm:retr,llm:summ --variant control --model "$M" --out results/llm_or_${TAG}_ctrl2.csv --dump-dir results/or_${TAG}_ctrl2 >> $LOG 2>&1
  echo "TABLEFILL_${TAG}_DONE $(date)" >> $LOG
else
  LOG=llm_or_tablefill_frontier.log
  gate 12
  for P in "openai/gpt-5.5 gpt55" "anthropic/claude-sonnet-5 sonnet5"; do set -- $P
    python3 run_suite.py $COMMON --policies llm:bank --variant control --model "$1" --out results/llm_or_$2_ctrl2.csv --dump-dir results/or_$2_ctrl2 >> $LOG 2>&1
    echo "FRONTIER_FLOOR_$2_DONE balance=$(bal) $(date)" >> $LOG
    gate 4
  done
  gate 30
  for P in "openai/gpt-5.5 gpt55" "anthropic/claude-sonnet-5 sonnet5"; do set -- $P
    python3 run_suite.py $COMMON --policies llm:bank,llm:sched2 --variant live --model "$1" --out results/llm_or_$2.csv --dump-dir results/or_$2 >> $LOG 2>&1
    python3 run_suite.py $COMMON --policies llm:sched2 --variant control --model "$1" --out results/llm_or_$2_ctrl2.csv --dump-dir results/or_$2_ctrl2 >> $LOG 2>&1
    echo "FRONTIER_LIVE_$2_DONE balance=$(bal) $(date)" >> $LOG
  done
  echo "TABLEFILL_FRONTIER_DONE $(date)" >> $LOG
fi
