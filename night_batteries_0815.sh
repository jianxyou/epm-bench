#!/bin/bash
# Night of 08-15: batteries 2 & 3 (run after battery 1 finishes).
set -x
cd /Users/jianxin/Desktop/my_project/embodied_pm

# Battery 2: window sweep — EAC as a function of window size (cancel-retention
# half-life curve). bank shows the leak, rrn is the control that should stay 0.
for W in 2 4 6 10 16; do
  python3 sched_geometry.py --policies bank,rrn --loads 1 --seeds 24 \
    --cancel-arms early,late --window $W \
    --out results/sched_geo_window.csv
done

# Battery 3: delay dose-response per policy (mechanical EXEC vs delay).
for D in 3 10 14; do
  python3 sched_geometry.py --policies bank,every5,rr,rrn,sight --loads 1 \
    --seeds 24 --cancel-arms none --delay $D \
    --out results/sched_geo_delay.csv
done

echo "NIGHT BATTERIES DONE"
