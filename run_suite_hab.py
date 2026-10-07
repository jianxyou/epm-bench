#!/usr/bin/env python
"""Execute policies over the frozen EPM-Bench suite (Habitat tier).

Run inside the conda 'habitat' env. Mirrors run_suite.py.
Scripted policies via pm_habitat.run_policy; window-bounded mock LLM tier via
pm_habitat.run_llm_tier(mock=True).

  python run_suite_hab.py --split dev --delay 10 --seeds 0:50 \
      --policies oracle,patroller,opportunistic,idle,deaf
  python run_suite_hab.py --split dev --delay 10 --seeds 0:50 \
      --policies mockllm:none,mockllm:bank,mockllm:rwim,mockllm:sched \
      --window 6
"""
import argparse
import csv
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import pm_habitat

FIELDS = ["ts", "suite", "engine", "split", "scene", "seed", "delay", "load",
          "variant", "twin_group", "policy", "window", "executed",
          "event_step", "first_visible_step", "exec_step", "cancelled",
          "cancel_step", "eac_strict", "chores_done", "steps_total"]

SCRIPTED = {"oracle", "negligent", "patroller", "opportunistic", "idle",
            "smartpatrol", "informed", "deaf"}


def to_spec(e):
    spec = dict(e["spec"])
    for k in ("start", "marker", "hot_anchor"):
        if spec.get(k) is not None:
            spec[k] = np.array(spec[k], dtype=np.float32)
    for k in ("waypoints", "lookouts"):
        if spec.get(k):
            spec[k] = [np.array(p, dtype=np.float32) for p in spec[k]]
    return spec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default=os.path.join(HERE, "suite",
                                                    "epm_v0.1_habitat.jsonl"))
    ap.add_argument("--split", default=None)
    ap.add_argument("--scene", default=None)
    ap.add_argument("--delay", type=int, default=None)
    ap.add_argument("--variant", default=None)
    ap.add_argument("--seeds", default=None, help="lo:hi (hi exclusive)")
    ap.add_argument("--policies", required=True)
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--window", type=int, default=6)
    ap.add_argument("--max-steps", type=int, default=60)
    ap.add_argument("--out", default=os.path.join(HERE, "results",
                                                  "suite_hab_v01.csv"))
    args = ap.parse_args()

    lo, hi = (None, None)
    if args.seeds:
        lo, hi = (int(x) for x in args.seeds.split(":"))
    eps = []
    for raw in open(args.suite):
        e = json.loads(raw)
        if args.split and e["split"] != args.split:
            continue
        if args.scene and e["scene"] != args.scene:
            continue
        if args.delay is not None and e["delay"] != args.delay:
            continue
        if lo is not None and not (lo <= e["seed"] < hi):
            continue
        eps.append(e)
    if not eps:
        raise SystemExit("no episodes match filter")

    policies = args.policies.split(",")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    new = not os.path.exists(args.out)
    n_done = 0
    t0 = time.time()
    envs = {}

    def get_env(scene):
        if scene not in envs:
            envs[scene] = pm_habitat.HabitatPMEnv(scene)
        return envs[scene]

    try:
        with open(args.out, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if new:
                w.writeheader()
            for pol in policies:
                allowed = (set(args.variant.split(",")) if args.variant
                           else ({"live", "cancel_early", "cancel_late"}
                                 if pol in SCRIPTED else
                                 {"control", "live", "cancel_early",
                                  "cancel_late"}))
                todo = [e for e in eps if e["variant"] in allowed]
                for j, e in enumerate(todo):
                    env = get_env(e["scene"])
                    spec = to_spec(e)
                    try:
                        if pol.startswith("mockllm:"):
                            chores = pm_habitat.run_llm_tier(
                                env, spec, mem=pol.split(":", 1)[1],
                                window=args.window,
                                max_steps=args.max_steps, mock=True)
                        else:
                            chores = pm_habitat.run_policy(
                                env, spec, pol, k=args.k,
                                max_steps=args.max_steps)
                    except Exception as ex:
                        print(f"{pol} {e['twin_group']} {e['variant']}: "
                              f"{type(ex).__name__} {str(ex)[:100]}",
                              flush=True)
                        continue
                    adj = env.adjudicate()
                    row = {"ts": int(time.time()), "suite": e["suite"],
                           "engine": e["engine"], "split": e["split"],
                           "scene": e["scene"], "seed": e["seed"],
                           "delay": e["delay"], "load": e["load"],
                           "variant": e["variant"],
                           "twin_group": e["twin_group"],
                           "policy": (pol if not pol.startswith("mockllm:")
                                      else f"mockllm-{pol.split(':', 1)[1]}"),
                           "window": (args.window
                                      if pol.startswith("mockllm:") else ""),
                           "chores_done": chores, **adj}
                    w.writerow(row)
                    f.flush()
                    n_done += 1
                    if (j + 1) % 50 == 0:
                        rate = n_done / (time.time() - t0)
                        print(f"[{pol}] {j+1}/{len(todo)} ({rate:.2f} ep/s)",
                              flush=True)
                print(f"policy {pol} done ({n_done} total)", flush=True)
    finally:
        for env in envs.values():
            env.sim.close()
        print(f"TOTAL {n_done} episodes in {(time.time()-t0)/60:.1f} min "
              f"-> {args.out}")


if __name__ == "__main__":
    main()
