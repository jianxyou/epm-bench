#!/bin/bash
set -x
cd "$(dirname "$0")"
source $HOME/miniforge3-x86/bin/activate
conda activate habitat
OUT=results/ladder.csv
P="python pm_habitat.py"
echo "=== F1 ladder, uniform spawn, delay 10 ==="
for pol in negligent opportunistic idle oracle; do
  $P --policy $pol --episodes 24 --out $OUT || true
done
$P --policy patroller  --k 8 --episodes 24 --out $OUT || true
$P --policy smartpatrol --k 8 --episodes 24 --out $OUT || true
echo "=== F2 ladder under hot-zone spawn (prior exists) ==="
for pol in opportunistic idle; do
  $P --policy $pol --episodes 24 --hot --out $OUT || true
done
$P --policy patroller  --k 8 --episodes 24 --hot --out $OUT || true
$P --policy smartpatrol --k 8 --episodes 24 --hot --out $OUT || true
$P --policy informed   --k 8 --episodes 24 --hot --out $OUT || true
echo "=== F3 hard delay 20 ==="
for pol in opportunistic idle; do
  $P --policy $pol --episodes 24 --delay 20 --out $OUT || true
done
$P --policy smartpatrol --k 8 --episodes 24 --delay 20 --out $OUT || true
echo "LADDER_DONE $(date)"
