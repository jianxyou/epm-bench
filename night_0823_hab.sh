#!/bin/bash
# Night of 08-23: Habitat battery over the frozen v0.1 suite + F8 parity sweep.
set -x
cd /Users/jianxin/Desktop/my_project/embodied_pm
source $HOME/miniforge3-x86/bin/activate
conda activate habitat
OUT=results/suite_hab_v01.csv

# 1. Headline (dev, delay 10): scripted ladder, n=50
python run_suite_hab.py --split dev --delay 10 --seeds 0:50 \
  --policies oracle,negligent,patroller,opportunistic,idle,deaf --out $OUT

# 2. Headline: mock LLM tier, all variants, n=50
python run_suite_hab.py --split dev --delay 10 --seeds 0:50 \
  --policies mockllm:none,mockllm:bank,mockllm:rwim,mockllm:sched \
  --window 6 --out $OUT

# 3. Delay curve (6/14), n=24
for D in 6 14; do
  python run_suite_hab.py --split dev --delay $D --seeds 0:24 \
    --policies patroller,opportunistic,mockllm:bank \
    --variant live,cancel_late --out $OUT
done

# 4. Test split (castle, delay 10), n=24
python run_suite_hab.py --split test --seeds 100:124 \
  --policies oracle,patroller,mockllm:bank,mockllm:sched \
  --variant live,cancel_late --out $OUT

# 5. F8 parity: EAC-vs-window sweep (bank leak vs sched/rwim controls), n=48
for W in 2 4 6 10 16; do
  python run_suite_hab.py --split dev --delay 10 --seeds 0:48 \
    --policies mockllm:bank,mockllm:rwim,mockllm:sched --window $W \
    --variant cancel_early,cancel_late \
    --out results/hab_window_sweep.csv
done

echo "HAB_BATTERY_DONE $(date)"
