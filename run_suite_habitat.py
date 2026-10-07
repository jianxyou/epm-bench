#!/usr/bin/env python3
"""LLM tier over the frozen Habitat suite (suite/epm_v0.1_habitat.jsonl).
Run with the habitat conda env:
  ~/miniforge3-x86/envs/habitat/bin/python run_suite_habitat.py --split dev --delay 10 \\
      --seeds 0:50 --mems bank,sched2 --model openai/gpt-4o-mini --out results/hab_or_gpt4omini.csv
One CSV row per episode, flushed immediately; --resume skips finished ones."""
import argparse, csv, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import pm_habitat as H

FIELDS = ["ts", "suite", "engine", "split", "scene", "seed", "delay", "load", "variant",
          "twin_group", "policy", "model", "executed", "event_step", "first_visible_step",
          "exec_step", "cancelled", "cancel_step", "eac_strict", "steps_total",
          "chores_done", "api_tokens"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default=os.path.join(HERE, "suite", "epm_v0.1_habitat.jsonl"))
    ap.add_argument("--split", default="dev"); ap.add_argument("--scene", default=None)
    ap.add_argument("--delay", type=int, default=10)
    ap.add_argument("--variant", default="control,live,cancel_early,cancel_late")
    ap.add_argument("--seeds", default="0:50"); ap.add_argument("--mems", required=True)
    ap.add_argument("--model", required=True); ap.add_argument("--window", type=int, default=6)
    ap.add_argument("--max-steps", type=int, default=60)
    ap.add_argument("--out", required=True); ap.add_argument("--dump-dir", default=None)
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.seeds.split(":")); variants = set(a.variant.split(","))
    eps = []
    for raw in open(a.suite):
        e = json.loads(raw)
        if e["split"] != a.split or e["delay"] != a.delay or e["variant"] not in variants: continue
        if a.scene and e["scene"] != a.scene: continue
        if not (lo <= e["seed"] < hi): continue
        eps.append(e)
    if not eps: raise SystemExit("no episodes match filter")
    done = set()
    if a.resume and os.path.exists(a.out):
        for r in csv.DictReader(open(a.out)): done.add((r["policy"], r["twin_group"], r["variant"]))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    if a.dump_dir: os.makedirs(a.dump_dir, exist_ok=True)
    new = not os.path.exists(a.out)
    envs = {}; n = 0; t0 = time.time()
    with open(a.out, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new: w.writeheader()
        for mem in a.mems.split(","):
            pol = f"llm-{mem}"
            for e in eps:
                if (pol, e["twin_group"], e["variant"]) in done: continue
                env = envs.get(e["scene"]) or envs.setdefault(e["scene"], H.HabitatPMEnv(e["scene"]))
                trace = [] if a.dump_dir else None
                for attempt in (1, 2):
                    try:
                        chores = H.run_llm_tier(env, e["spec"], mem=mem, window=a.window,
                                                max_steps=a.max_steps, mock=False,
                                                model=a.model, trace=trace)
                        break
                    except SystemExit: raise
                    except Exception as ex:
                        print(f"{pol} {e['twin_group']} {e['variant']} attempt{attempt}: {type(ex).__name__} {str(ex)[:100]}", flush=True)
                        chores = None
                if chores is None: continue
                adj = env.adjudicate()
                w.writerow({"ts": int(time.time()), "suite": e["suite"], "engine": "habitat",
                            "split": e["split"], "scene": e["scene"], "seed": e["seed"],
                            "delay": e["delay"], "load": e["load"], "variant": e["variant"],
                            "twin_group": e["twin_group"], "policy": pol, "model": a.model,
                            "chores_done": chores, "api_tokens": getattr(env, "api_tokens", 0), **adj})
                f.flush(); n += 1
                if a.dump_dir:
                    name = e["twin_group"].replace("/", "_") + f"_{e['variant']}_{pol}.trace.jsonl"
                    with open(os.path.join(a.dump_dir, name), "w") as g:
                        for r in trace: g.write(json.dumps(r) + "\n")
                if n % 20 == 0: print(f"[{pol}] {n} eps, {(time.time()-t0)/n:.0f}s/ep", flush=True)
            print(f"mem {mem} done ({n} total)", flush=True)
    print(f"TOTAL {n} episodes in {(time.time()-t0)/60:.1f} min -> {a.out}")

if __name__ == "__main__":
    main()
