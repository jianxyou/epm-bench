#!/usr/bin/env python3
"""Narrated replay of ONE episode from the frozen suite. Usage:
  python3 walk_one.py                     # seed 1, naive store, late cancel
  python3 walk_one.py --seed 3 --mem sched --variant cancel_late
  python3 walk_one.py --seed 5 --mem bank --variant live
mem: none | bank (naive store) | sched (typed store) | rwim
variant: live | cancel_early | cancel_late | control
Prints every step: what the agent reads, remembers, and does; then the verdict.
"""
import argparse, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agents
from env import ThorPMEnv

ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--mem", default="bank")
ap.add_argument("--variant", default="cancel_late")
ap.add_argument("--window", type=int, default=6)
a = ap.parse_args()

eps = [json.loads(l) for l in open(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "suite/epm_v0.1_thor.jsonl"))]
e = next(x for x in eps if x["scene"] == "FloorPlan1" and x["seed"] == a.seed
         and x["delay"] == 6 and x["load"] == 1 and x["variant"] == a.variant)
spec = dict(e["spec"]); spec["chores"] = [tuple(c) for c in spec["chores"]]
if a.variant == "control":
    spec["has_intention"] = False
print("简报:", spec["briefing"][:150], "...")
it = spec["intentions"][0]
print(f"剧本: 第{it['event_step']}步世界打开{it['trigger_type']}(视野外)"
      + (f", 第{it['cancel_step']}步用户取消" if it.get("cancel_step") else ", 无取消")
      + f" | 考生: {a.mem}, 窗口={a.window}行")
print("=" * 100)
envh = ThorPMEnv(size=128)
try:
    envh.reset(spec, scene="FloorPlan1")
    agents.run_mock_llm(envh, spec, mem=a.mem, window=a.window, narrate=True)
    adj = envh.adjudicate()
    print("=" * 100)
    if it.get("cancel_step"):
        print(f"判分: 执行步={adj['exec_step']} 取消步={adj['cancel_step']} -> "
              f"EAC={'违规!' if adj['eac_strict'] else '清白'}")
    else:
        print(f"判分: 执行步={adj['exec_step']} -> "
              f"EXEC={'完成' if adj['executed'] else '未完成'}")
finally:
    envh.stop()
