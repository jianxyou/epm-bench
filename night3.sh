#!/bin/bash
# Battery E: big-N consolidation + focality + visibility x delay interaction.
# caffeinate keeps the Mac (and Unity) awake — the ABC battery stalled ~2.7h on App Nap.
cd "$(dirname "$0")"
OUT=results/night3.csv
echo "=== E1 frontier n=24 $(date) ==="
for k in 2 3 4 6 8 12; do
  python3 run_pilot.py --policy patroller --k $k --episodes 24 --out $OUT || true
done
echo "=== E2 delay sweep n=24 $(date) ==="
for d in 3 6 10 14 20; do
  python3 run_pilot.py --policy opportunistic --episodes 24 --delay $d --out $OUT || true
  python3 run_pilot.py --policy patroller --k 4 --episodes 24 --delay $d --out $OUT || true
done
echo "=== E3 visibility x hard delay (oppo, delay 14) $(date) ==="
for v in 0.8 1.5 2.5; do
  python3 run_pilot.py --policy opportunistic --episodes 24 --delay 14 --visibility $v --out $OUT || true
done
echo "=== E4 load n=24 $(date) ==="
for n in 1 2 3; do
  python3 run_pilot.py --policy patroller --k 4 --episodes 24 --load $n --out $OUT || true
  python3 run_pilot.py --policy opportunistic --episodes 24 --load $n --out $OUT || true
done
echo "=== E5 focality controlled (oppo, delay 10) $(date) ==="
python3 run_pilot.py --policy opportunistic --episodes 24 --delay 10 --trigger CoffeeMachine --out $OUT || true
python3 run_pilot.py --policy opportunistic --episodes 24 --delay 10 --trigger Microwave --out $OUT || true
python3 run_pilot.py --policy opportunistic --episodes 24 --delay 10 --trigger Toaster --out $OUT || true
echo "NIGHT3_DONE $(date)"
