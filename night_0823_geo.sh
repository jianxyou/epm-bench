#!/bin/bash
# Night of 08-23: sched-geometry grid at n=48 WITH three-regime grading dump.
# Feeds (a) F16-F19 replication at n=48 in one clean file, (b) the P4
# grading-ablation analysis (world vs QA vs selection on identical episodes).
set -x
cd /Users/jianxin/Desktop/my_project/embodied_pm
CSV=results/sched_geo_0823.csv
DUMP=results/grading_records_0823.jsonl

# main grid: 5 policies x loads 1-3 x cancel early/late x 48 seeds, window 6
python3 sched_geometry.py --policies bank,every5,rr,rrn,sight \
  --loads 1,2,3 --seeds 48 --cancel-arms early,late --window 6 \
  --out $CSV --grade-dump $DUMP

# no-cancel arm for EXEC floors (loads 1-3, 48 seeds)
python3 sched_geometry.py --policies bank,every5,rr,rrn,sight \
  --loads 1,2,3 --seeds 48 --cancel-arms none --window 6 \
  --out $CSV --grade-dump $DUMP

# window sweep for cancel-retention half-life (bank leak vs rrn control)
for W in 2 4 10 16; do
  python3 sched_geometry.py --policies bank,rrn --loads 1 --seeds 48 \
    --cancel-arms early,late --window $W \
    --out $CSV --grade-dump $DUMP
done

echo "GEO_BATTERY_DONE $(date)"
