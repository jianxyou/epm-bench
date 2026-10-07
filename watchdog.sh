#!/bin/bash
# Every 5 min: if a run's log ends in a streak of >=6 APIConnectionError lines,
# the process's HTTP pool is dead -> kill just that python (found via lsof on the
# log). Its queue script moves to the next segment; run_fill.sh recovers the gap.
cd /Users/jianxin/Desktop/my_project/embodied_pm
while true; do
  for log in llm_or_sched2.log llm_or_tierA.log llm_or_tierC.log queue_0913.log; do
    [ -f "$log" ] || continue
    streak=$(tail -8 "$log" | grep -c "APIConnectionError")
    if [ "$streak" -ge 6 ]; then
      for pid in $(pgrep -f 'MacOS/Python run_s'); do
        if lsof -p "$pid" 2>/dev/null | grep -q "$log"; then
          echo "$(date) WATCHDOG killed $pid (dead pool, log=$log)" >> watchdog.log
          kill "$pid"
        fi
      done
    fi
  done
  sleep 300
done
