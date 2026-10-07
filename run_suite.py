#!/usr/bin/env python3
"""Execute policies over the frozen EPM-Bench suite (THOR tier).

Reads suite/epm_v0.1_thor.jsonl, filters cells, runs policies, writes one CSV
row per (episode, policy) keyed by twin_group so twins join across variants.

Scripted policies run on live/cancel variants (their intention knowledge is
coded, so control is meaningless for them). Mock policies (window-bounded rule
reader) run on all four variants including control.

Examples:
  python3 run_suite.py --split dev --delay 6 --load 1 --seeds 0:50 \
      --policies oracle,negligent,opportunistic,patroller,adaptive,deaf
  python3 run_suite.py --split dev --delay 6 --load 1 --seeds 0:50 \
      --policies mock:bank,mock:sched --window 6
  python3 run_suite.py --split test --policies oracle,patroller,adaptive
Optional per-episode event-log dump for the grading ablation: --dump-dir.
"""
import argparse
import csv
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import agents
from env import ThorPMEnv

FIELDS = ["ts", "suite", "engine", "split", "scene", "seed", "delay", "load",
          "variant", "twin_group", "policy", "executed", "executed_frac",
          "event_step", "first_visible_step", "exec_step", "cancelled",
          "cancel_step", "executed_after_cancel", "eac_strict",
          "n_intentions", "chores_done", "steps_total", "api_tokens"]

SCRIPTED = {"oracle", "negligent", "opportunistic", "patroller", "adaptive",
            "deaf"}


def run_policy(envh, spec, policy, k, window, model=None, vision=False,
               trace_path=None, mem_model=None, probe=False):
    if policy == "oracle":
        return agents.run_oracle(envh, spec)
    if policy == "negligent":
        return agents.run_negligent(envh, spec)
    if policy == "opportunistic":
        return agents.run_opportunistic(envh, spec)
    if policy == "patroller":
        return agents.run_patroller(envh, spec, k=k)
    if policy == "deaf":
        return agents.run_deaf_patroller(envh, spec, k=k)
    if policy == "adaptive":
        return agents.run_adaptive(envh, spec, k=k)
    if policy.startswith("mock:"):
        return agents.run_mock_llm(envh, spec, mem=policy.split(":", 1)[1],
                                   window=window)
    if policy.startswith("llm:"):
        return agents.run_llm(envh, spec, mem=policy.split(":", 1)[1],
                              model=model, window=window, vision=vision,
                              trace_path=trace_path, mem_model=mem_model,
                              probe=probe)
    raise SystemExit(f"unknown policy {policy}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default=os.path.join(HERE, "suite",
                                                    "epm_v0.1_thor.jsonl"))
    ap.add_argument("--split", default=None)
    ap.add_argument("--scene", default=None)
    ap.add_argument("--delay", type=int, default=None)
    ap.add_argument("--load", type=int, default=None)
    ap.add_argument("--variant", default=None,
                    help="comma list; default live,cancel_early,cancel_late "
                         "for scripted and all four for mock")
    ap.add_argument("--seeds", default=None, help="lo:hi (hi exclusive)")
    ap.add_argument("--policies", required=True)
    ap.add_argument("--k", type=int, default=6)
    ap.add_argument("--window", type=int, default=6)
    ap.add_argument("--model", default=agents.MODEL_DEFAULT,
                    help="for llm:* policies; 'vendor/name' routes to OpenRouter")
    ap.add_argument("--vision", action="store_true",
                    help="llm:* policies see RGB frames instead of text")
    ap.add_argument("--out", default=os.path.join(HERE, "results",
                                                  "suite_thor.csv"))
    ap.add_argument("--dump-dir", default=None,
                    help="write per-episode event-log JSON here")
    ap.add_argument("--resume", action="store_true",
                    help="skip episodes already present in --out")
    ap.add_argument("--obs-v2", action="store_true", help="toggleable objects first in observe() (v0.2); default v0.1 ordering")
    ap.add_argument("--probe", action="store_true",
                    help="ask the actor each step whether the instruction is still in force (logged, not shown to it)")
    ap.add_argument("--mem-model", default=None,
                    help="separate model for the memory agent (rwim*/summ)")
    ap.add_argument("--size", type=int, default=128,
                    help="render size in px (use >=300 with --vision)")
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
        if args.load is not None and e["load"] != args.load:
            continue
        if lo is not None and not (lo <= e["seed"] < hi):
            continue
        eps.append(e)
    if not eps:
        raise SystemExit("no episodes match filter")

    policies = args.policies.split(",")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    # resume: skip cells already present in the output CSV
    done = set()
    if args.resume and os.path.exists(args.out):
        for r in csv.DictReader(open(args.out)):
            done.add((r["policy"], r["twin_group"], r["variant"]))
        if done:
            print(f"resume: {len(done)} episodes already in {args.out}",
                  flush=True)
    if args.dump_dir:
        os.makedirs(args.dump_dir, exist_ok=True)
    new = not os.path.exists(args.out)
    envh = ThorPMEnv(size=args.size, toggle_first=args.obs_v2)
    n_done = 0
    t0 = time.time()
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
                    pol_name = None
                    if pol.startswith("llm:"):
                        mm = (("@" + args.mem_model.split("/")[-1][:14])
                              if args.mem_model else "")
                        pol_name = ("llm-" + pol.split(":", 1)[1] + mm
                                    + ("-rgb" if args.vision else "")
                                    + ("-probe" if args.probe else ""))
                    if pol_name and (pol_name, e["twin_group"],
                                     e["variant"]) in done:
                        continue
                    spec = dict(e["spec"])
                    spec["chores"] = [tuple(c) for c in spec["chores"]]
                    if e["variant"] == "control":
                        spec["has_intention"] = False
                    for attempt in (1, 2):
                        try:
                            envh.reset(spec, scene=e["scene"])
                            tp = None
                            if args.dump_dir and pol.startswith("llm:"):
                                tp = os.path.join(
                                    args.dump_dir,
                                    e["twin_group"].replace("/", "_")
                                    + f"_{e['variant']}_{pol_name}"
                                    + ".trace.jsonl")
                            info = run_policy(envh, spec, pol, args.k,
                                              args.window, model=args.model,
                                              vision=args.vision, trace_path=tp,
                                              mem_model=args.mem_model,
                                              probe=args.probe)
                            break
                        except SystemExit:
                            raise
                        except Exception as ex:
                            print(f"{pol} {e['twin_group']} {e['variant']} "
                                  f"attempt{attempt}: {type(ex).__name__} "
                                  f"{str(ex)[:100]}", flush=True)
                            try:
                                envh.stop()
                            except Exception:
                                pass
                            envh = ThorPMEnv(size=args.size, toggle_first=args.obs_v2)
                            info = None
                    if info is None:
                        continue
                    adj = envh.adjudicate()
                    per = adj.pop("per_intention", None)
                    chores = sum(1 for r in envh.log
                                 if r["action"] == "put" and r["ok"])
                    row = {"ts": int(time.time()), "suite": e["suite"],
                           "engine": e["engine"], "split": e["split"],
                           "scene": e["scene"], "seed": e["seed"],
                           "delay": e["delay"], "load": e["load"],
                           "variant": e["variant"],
                           "twin_group": e["twin_group"],
                           "policy": info["policy"], "chores_done": chores,
                           "api_tokens": info.get("api_tokens", 0), **adj}
                    w.writerow(row)
                    f.flush()
                    n_done += 1
                    if args.dump_dir:
                        dump = {"episode": {k: e[k] for k in
                                            ("suite", "engine", "split",
                                             "scene", "seed", "delay", "load",
                                             "variant", "twin_group")},
                                "policy": info["policy"],
                                "adjudication": {**adj, "per_intention": per},
                                "log": [{k: r[k] for k in
                                         ("t", "action", "arg", "ok",
                                          "trigger_on", "trigger_visible")}
                                        for r in envh.log]}
                        name = (e["twin_group"].replace("/", "_")
                                + f"_{e['variant']}_{info['policy']}.json")
                        with open(os.path.join(args.dump_dir, name), "w") as g:
                            json.dump(dump, g)
                    if (j + 1) % 25 == 0:
                        rate = n_done / (time.time() - t0)
                        print(f"[{pol}] {j+1}/{len(todo)} "
                              f"({rate:.2f} ep/s)", flush=True)
                print(f"policy {pol} done ({n_done} total)", flush=True)
    finally:
        envh.stop()
        dt = time.time() - t0
        print(f"TOTAL {n_done} episodes in {dt/60:.1f} min -> {args.out}")


if __name__ == "__main__":
    main()
