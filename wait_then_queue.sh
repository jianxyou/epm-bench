#!/bin/bash
# Wait for the running DeepSeek cancellation job, then run the queue.
while pgrep -f "run_suite.py.*deepseek.*cancel_early,cancel_late" > /dev/null; do
  sleep 120
done
bash /Users/jianxin/Desktop/my_project/embodied_pm/run_queue_0913.sh
