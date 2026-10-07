#!/bin/bash
# Overnight battery, 2026-08-05. No API needed. Fail-soft per block.
cd "$(dirname "$0")"
OUT=results/night.csv
echo "=== BATTERY A: scenes x floors $(date) ==="
for s in FloorPlan1 FloorPlan2 FloorPlan3 FloorPlan4 FloorPlan5 FloorPlan6 FloorPlan7 FloorPlan8 FloorPlan9 FloorPlan10; do
  python3 run_pilot.py --policy oracle        --episodes 2 --scene $s --out $OUT || true
  python3 run_pilot.py --policy negligent     --episodes 1 --scene $s --out $OUT || true
  python3 run_pilot.py --policy opportunistic --episodes 1 --scene $s --out $OUT || true
done
echo "=== BATTERY B: cost-compliance frontier $(date) ==="
for k in 2 3 4 6 8 12; do
  python3 run_pilot.py --policy patroller --k $k --episodes 8 --out $OUT || true
  python3 run_pilot.py --policy patroller --k $k --episodes 8 --cancel late --out $OUT || true
done
python3 run_pilot.py --policy deaf --k 4 --episodes 8 --cancel late --out $OUT || true
python3 run_pilot.py --policy opportunistic --episodes 8 --out $OUT || true
python3 run_pilot.py --policy opportunistic --episodes 8 --cancel late --out $OUT || true
echo "=== BATTERY C: delay sweep (patroller k=4, opportunistic) $(date) ==="
for d in 3 10 14 20; do
  python3 run_pilot.py --policy patroller --k 4 --episodes 6 --delay $d --out $OUT || true
  python3 run_pilot.py --policy opportunistic --episodes 6 --delay $d --out $OUT || true
done
echo "NIGHT_DONE $(date)"
