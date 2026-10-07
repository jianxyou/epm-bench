#!/usr/bin/env python3
"""Runner. Examples:
  python3 run_pilot.py --smoke                       # oracle + negligent, 1 seed
  python3 run_pilot.py --policy oracle --episodes 5
  python3 run_pilot.py --policy patroller --k 6 --episodes 5 --cancel late
  python3 run_pilot.py --policy llm --mem rwim --episodes 5   # needs credits
CSV -> results/pilot.csv (append), one row per episode.
"""
import argparse
import csv
import os
import sys
import time

import tasks
from env import ThorPMEnv
import agents

FIELDS = ["ts", "policy", "seed", "scene", "delay", "cancel", "trigger",
          "visibility", "n_intentions", "event_step", "first_visible_step",
          "exec_step", "executed", "executed_frac", "cancelled", "cancel_step",
          "executed_after_cancel", "eac_strict", "trigger_on_route",
          "steps_total", "chores_done", "api_tokens"]


def run_one(envh, policy, seed, delay, cancel, k, mem, model, window,
            scene="FloorPlan1", trigger=None, n_intentions=1, visibility=1.5,
            control=False, vision=False):
    types = envh.scan_types(scene)
    spec = tasks.build_episode_for_scene(types, seed=seed, delay=delay,
                                         cancel=cancel, trigger=trigger,
                                         n_intentions=n_intentions)
    if spec is None:
        return None
    if control:
        spec["briefing"] = ("Your chores, in order: "
                            + "; ".join(f"put the {a} into the {b}"
                                        for a, b in spec["chores"]) + ".")
    envh.reset(spec, scene=scene)
    if policy == "oracle":
        info = agents.run_oracle(envh, spec)
    elif policy == "negligent":
        info = agents.run_negligent(envh, spec)
    elif policy == "opportunistic":
        info = agents.run_opportunistic(envh, spec)
    elif policy == "patroller":
        info = agents.run_patroller(envh, spec, k=k)
    elif policy == "deaf":
        info = agents.run_deaf_patroller(envh, spec, k=k)
    elif policy == "llm":
        import os as _os
        tp = (_os.path.join("results", "traces", f"{mem}_s{seed}.jsonl")
              if _os.environ.get("PM_TRACE") else None)
        info = agents.run_llm(envh, spec, mem=mem, model=model, window=window,
                              trace_path=tp, vision=vision)
    elif policy == "adaptive":
        info = agents.run_adaptive(envh, spec, k=k)
    elif policy == "mock":
        info = agents.run_mock_llm(envh, spec, mem=mem, window=window)
    else:
        raise SystemExit(f"unknown policy {policy}")
    adj = envh.adjudicate()
    adj.pop("per_intention", None)
    chores_done = sum(1 for r in envh.log if r["action"] == "put" and r["ok"])
    if control:
        info["policy"] += "-ctrl"
    row = {"ts": int(time.time()), "policy": info["policy"], "seed": seed,
           "scene": scene, "delay": delay, "cancel": cancel or "none",
           "trigger": spec["intention"]["trigger_type"] + ("" if not control else ""),
           "visibility": visibility,
           "trigger_on_route": spec["intention"]["trigger_type"]
               in {b for _a, b in spec["chores"]},
           "chores_done": chores_done,
           "api_tokens": info["api_tokens"], **adj}
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="oracle")
    ap.add_argument("--episodes", type=int, default=1)
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--delay", type=int, default=6)
    ap.add_argument("--cancel", default=None, choices=[None, "early", "late"])
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--mem", default="none", choices=["none", "bank", "rwim", "rwim2", "sched"])
    ap.add_argument("--model", default=agents.MODEL_DEFAULT)
    ap.add_argument("--window", type=int, default=6)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--scene", default="FloorPlan1")
    ap.add_argument("--trigger", default=None)
    ap.add_argument("--load", type=int, default=1, dest="n_intentions")
    ap.add_argument("--visibility", type=float, default=1.5)
    ap.add_argument("--control", action="store_true",
                    help="strip the intention from the briefing")
    ap.add_argument("--vision", action="store_true")
    ap.add_argument("--out", default="results/pilot.csv")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    new = not os.path.exists(args.out)
    envh = ThorPMEnv(visibility=args.visibility)
    rows = []
    try:
        if args.smoke:
            plan = [("oracle", 0, None), ("negligent", 0, None)]
            for pol, s, canc in plan:
                r = run_one(envh, pol, s, args.delay, canc, args.k, args.mem,
                            args.model, args.window, scene=args.scene)
                if r is None:
                    continue
                rows.append(r)
                print({k: r[k] for k in ("policy", "executed",
                                          "first_visible_step", "exec_step",
                                          "steps_total")})
        else:
            for i in range(args.episodes):
                for attempt in (1, 2):
                    try:
                        r = run_one(envh, args.policy, args.seed0 + i,
                                    args.delay, args.cancel, args.k, args.mem,
                                    args.model, args.window, scene=args.scene,
                                    trigger=args.trigger,
                                    n_intentions=args.n_intentions,
                                    visibility=args.visibility,
                                    control=args.control, vision=args.vision)
                        break
                    except SystemExit:
                        raise
                    except Exception as e:
                        print(f"episode {i} attempt {attempt} failed: "
                              f"{type(e).__name__}: {str(e)[:120]}")
                        try:
                            envh.stop()
                        except Exception:
                            pass
                        envh = ThorPMEnv(visibility=args.visibility)
                        r = None
                if r is None:
                    print(f"scene {args.scene}: no valid episode, skipped")
                    break
                rows.append(r)
                print({k: r[k] for k in ("policy", "seed", "scene", "executed",
                                          "executed_after_cancel", "exec_step",
                                          "chores_done")})
    finally:
        envh.stop()
        with open(args.out, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if new:
                w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"wrote {len(rows)} rows -> {args.out}")


if __name__ == "__main__":
    main()
