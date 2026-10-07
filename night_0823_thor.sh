#!/bin/bash
# Night of 08-23: THOR battery over the frozen v0.1 suite.
# Headline cells at n=50, axis curves at n=24, test-split generalization n=24.
set -x
cd /Users/jianxin/Desktop/my_project/embodied_pm
OUT=results/suite_thor_v01.csv

# 1. Headline cell (dev, delay 6, load 1): scripted ladder, n=50
python3 run_suite.py --split dev --delay 6 --load 1 --seeds 0:50 \
  --policies oracle,negligent,opportunistic,patroller,adaptive,deaf \
  --out $OUT

# 2. Headline cell: mock tier (all four variants incl control), n=50
python3 run_suite.py --split dev --delay 6 --load 1 --seeds 0:50 \
  --policies mock:none,mock:bank,mock:sched --window 6 \
  --out $OUT

# 3. Delay dose-response (3/10/14), live+cancel_late, n=24
for D in 3 10 14; do
  python3 run_suite.py --split dev --delay $D --load 1 --seeds 0:24 \
    --policies patroller,opportunistic,adaptive,mock:bank \
    --variant live,cancel_late --out $OUT
done

# 4. Load curve (2/3), delay 6, n=24
for L in 2 3; do
  python3 run_suite.py --split dev --delay 6 --load $L --seeds 0:24 \
    --policies patroller,adaptive,mock:bank,mock:sched \
    --variant live,cancel_late --out $OUT
done

# 5. Test-split generalization (FloorPlan2/3/4, delay 6, load 1), n=24
python3 run_suite.py --split test --delay 6 --load 1 --seeds 100:124 \
  --policies oracle,patroller,adaptive,mock:bank,mock:sched \
  --variant live,cancel_late --out $OUT

echo "THOR_BATTERY_DONE $(date)"
