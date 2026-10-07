#!/bin/bash
# Habitat battery: multi-room apartment. Run inside conda habitat env.
set -x
cd "$(dirname "$0")"
source $HOME/miniforge3-x86/bin/activate
conda activate habitat
OUT=results/habitat3.csv
P="python pm_habitat.py"
echo "=== H0 smoke ==="
$P --policy oracle --episodes 3 --out $OUT || exit 1
echo "=== H1 solvability + floors (delay 10) ==="
$P --policy oracle        --episodes 24 --out $OUT || true
$P --policy negligent     --episodes 24 --out $OUT || true
$P --policy opportunistic --episodes 24 --out $OUT || true
echo "=== H2 frontier: patrol k sweep ==="
for k in 4 8 16; do
  $P --policy patroller --k $k --episodes 24 --out $OUT || true
  $P --policy patroller --k $k --episodes 24 --cancel late --out $OUT || true
done
echo "=== H3 delay sweep ==="
for d in 5 10 20 30; do
  $P --policy opportunistic --episodes 24 --delay $d --out $OUT || true
  $P --policy patroller --k 8 --episodes 24 --delay $d --out $OUT || true
done
echo "=== H4 cancellation validity ==="
$P --policy deaf --k 8 --episodes 24 --cancel late --out $OUT || true
$P --policy opportunistic --episodes 24 --cancel late --out $OUT || true
$P --policy opportunistic --episodes 24 --cancel early --out $OUT || true
echo "=== H5 second scene (skokloster: big open hall) ==="
$P --policy oracle        --episodes 12 --scene skokloster-castle --out $OUT || true
$P --policy opportunistic --episodes 12 --scene skokloster-castle --out $OUT || true
$P --policy patroller --k 8 --episodes 12 --scene skokloster-castle --out $OUT || true
echo "HABITAT_NIGHT_DONE $(date)"
