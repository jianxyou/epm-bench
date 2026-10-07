#!/bin/bash
# Battery D: visibility (salience) x load (multi-intention) x selective cancel.
cd "$(dirname "$0")"
OUT=results/night2.csv
echo "=== D1 visibility sweep $(date) ==="
for v in 0.8 1.5 2.5; do
  python3 run_pilot.py --policy opportunistic --episodes 8 --visibility $v --out $OUT || true
  python3 run_pilot.py --policy patroller --k 6 --episodes 8 --visibility $v --out $OUT || true
done
echo "=== D2 intention load $(date) ==="
for n in 1 2 3; do
  python3 run_pilot.py --policy patroller --k 4 --episodes 8 --load $n --out $OUT || true
  python3 run_pilot.py --policy opportunistic --episodes 8 --load $n --out $OUT || true
done
echo "=== D3 selective revocation (load 2, cancel first only) $(date) ==="
python3 run_pilot.py --policy patroller --k 4 --episodes 8 --load 2 --cancel late --out $OUT || true
python3 run_pilot.py --policy opportunistic --episodes 8 --load 2 --cancel late --out $OUT || true
python3 run_pilot.py --policy deaf --k 4 --episodes 8 --load 2 --cancel late --out $OUT || true
echo "=== D4 early cancel + deaf breadth $(date) ==="
python3 run_pilot.py --policy patroller --k 4 --episodes 8 --cancel early --out $OUT || true
python3 run_pilot.py --policy opportunistic --episodes 8 --cancel early --out $OUT || true
python3 run_pilot.py --policy deaf --k 2 --episodes 8 --cancel late --out $OUT || true
python3 run_pilot.py --policy deaf --k 8 --episodes 8 --cancel late --out $OUT || true
echo "NIGHT2_DONE $(date)"
