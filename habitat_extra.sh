#!/bin/bash
set -x
cd "$(dirname "$0")"
source $HOME/miniforge3-x86/bin/activate
conda activate habitat
P="python pm_habitat.py"
echo "=== X1 revocation-eviction window sweep (bank, cancel late) ==="
for w in 3 6 12 24 48; do
  $P --policy llm --mem bank --window $w --episodes 24 --cancel late --out results/revoke_sweep.csv || true
done
echo "=== X2 van-gogh single-room ladder ==="
for pol in oracle negligent opportunistic; do
  $P --policy $pol --episodes 24 --scene van-gogh-room --delay 10 --out results/scenes.csv || true
done
$P --policy patroller   --k 8 --episodes 24 --scene van-gogh-room --delay 10 --out results/scenes.csv || true
$P --policy smartpatrol --k 8 --episodes 24 --scene van-gogh-room --delay 10 --out results/scenes.csv || true
echo "=== X3 skokloster smartpatrol ==="
$P --policy smartpatrol --k 8 --episodes 24 --scene skokloster-castle --delay 10 --out results/scenes.csv || true
$P --policy opportunistic --episodes 24 --scene skokloster-castle --delay 10 --out results/scenes.csv || true
echo "EXTRA_DONE $(date)"
