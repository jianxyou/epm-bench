#!/usr/bin/env python3
"""EPM-Bench v0.1 suite freezer: generate, validate, and hash the episode suite.

The suite is the benchmark artifact: frozen episode specs (JSONL) + manifest.
Specs are generated deterministically from seeds; simulators are only needed
once (THOR: to scan per-scene object types, cached; Habitat: navmesh sampling
at freeze time). After freezing, `validate` is pure-python and offline.

Layout (suite/):
  scene_types.json          cached THOR scan_types per scene
  epm_v0.1_thor.jsonl       one line per concrete episode (variant expanded)
  epm_v0.1_habitat.jsonl    (written by freeze-habitat inside the conda env)
  MANIFEST.json             sha256 per file, generation params, versions

Episode line schema (shared keys):
  {suite, engine, split, scene, seed, delay, load, variant, twin_group, spec}
  variant in {control, live, cancel_early, cancel_late}
  twin_group = "{engine}/{scene}/s{seed}/d{delay}/l{load}" (join key for
  matched control/live/cancelled twins)

Commands:
  python3 suite.py freeze-thor              # needs ai2thor (default python3)
  python  suite.py freeze-habitat           # run inside conda 'habitat' env
  python3 suite.py validate                 # offline structural checks + MANIFEST
  python3 suite.py audit-thor --n 5         # sampled oracle solvability audit
  python  suite.py audit-habitat --n 5      # same, habitat side
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SUITE_DIR = os.path.join(HERE, "suite")
VERSION = "0.1"

# ---- frozen design (documented in MANIFEST) ----
THOR_DEV_SCENE = "FloorPlan1"
# test scenes: lowest-numbered audited scenes != dev with full trigger/chore
# support, chosen deterministically at freeze time from the audited ten.
THOR_AUDITED = [f"FloorPlan{i}" for i in range(1, 11)]
THOR_DEV_SEEDS = range(0, 100)
THOR_TEST_SEEDS = range(100, 200)
THOR_DEV_DELAYS = [3, 6, 10, 14]
THOR_TEST_DELAYS = [6]
THOR_DEV_LOADS = [1, 2, 3]
THOR_TEST_LOADS = [1]
HAB_DEV_SCENE = "apartment_1"
HAB_TEST_SCENE = "skokloster-castle"
HAB_DEV_DELAYS = [6, 10, 14]
HAB_TEST_DELAYS = [10]
VARIANTS = ["control", "live", "cancel_early", "cancel_late"]
CANCEL_OF = {"control": None, "live": None,
             "cancel_early": "early", "cancel_late": "late"}


def jsonable(x):
    try:
        import numpy as np
        if isinstance(x, np.ndarray):
            return [float(v) for v in x]
        if isinstance(x, (np.floating, np.integer)):
            return x.item()
    except ImportError:
        pass
    if isinstance(x, dict):
        return {k: jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    return x


def line(engine, split, scene, seed, delay, load, variant, spec):
    return {"suite": f"epm_v{VERSION}", "engine": engine, "split": split,
            "scene": scene, "seed": seed, "delay": delay, "load": load,
            "variant": variant,
            "twin_group": f"{engine}/{scene}/s{seed}/d{delay}/l{load}",
            "spec": jsonable(spec)}


# ---------------- THOR ----------------
def freeze_thor():
    import tasks
    from env import ThorPMEnv
    os.makedirs(SUITE_DIR, exist_ok=True)
    types_path = os.path.join(SUITE_DIR, "scene_types.json")
    if os.path.exists(types_path):
        types_by_scene = json.load(open(types_path))
    else:
        envh = ThorPMEnv(size=128)
        types_by_scene = {}
        try:
            for sc in THOR_AUDITED:
                types_by_scene[sc] = envh.scan_types(sc)
                print(f"scanned {sc}: "
                      f"{len(types_by_scene[sc]['toggleable'])} toggleable",
                      flush=True)
        finally:
            envh.stop()
        json.dump(types_by_scene, open(types_path, "w"), indent=1, sort_keys=True)
    # deterministic test-scene choice: >=3 usable triggers and >=6 chore moves
    def usable(sc):
        t = types_by_scene[sc]
        trig = [x for x in tasks.TRIGGERS if x in t["toggleable"]]
        moves = [(a, b) for a, b in tasks.CHORE_MOVES
                 if a in t["pickupable"] and b in t["receptacle"]]
        return len(trig) >= 3 and len(moves) >= 6
    test_scenes = [sc for sc in THOR_AUDITED
                   if sc != THOR_DEV_SCENE and usable(sc)][:3]
    out = os.path.join(SUITE_DIR, f"epm_v{VERSION}_thor.jsonl")
    n, skipped = 0, 0
    with open(out, "w") as f:
        def emit(split, scene, seeds, delays, loads):
            nonlocal n, skipped
            for seed in seeds:
                for delay in delays:
                    for load in loads:
                        for variant in VARIANTS:
                            spec = tasks.build_episode_for_scene(
                                types_by_scene[scene], seed=seed, delay=delay,
                                cancel=CANCEL_OF[variant], n_intentions=load)
                            if spec is None:
                                skipped += 1
                                continue
                            if variant == "control":
                                spec = dict(spec)
                                spec["has_intention"] = False
                                spec["briefing"] = (
                                    "Your chores, in order: "
                                    + "; ".join(f"put the {a} into the {b}"
                                                for a, b in spec["chores"])
                                    + ".")
                            f.write(json.dumps(
                                line("thor", split, scene, seed, delay, load,
                                     variant, spec), sort_keys=True) + "\n")
                            n += 1
        emit("dev", THOR_DEV_SCENE, THOR_DEV_SEEDS, THOR_DEV_DELAYS,
             THOR_DEV_LOADS)
        for sc in test_scenes:
            emit("test", sc, THOR_TEST_SEEDS, THOR_TEST_DELAYS, THOR_TEST_LOADS)
    print(f"thor: wrote {n} episodes ({skipped} unsatisfiable skipped) -> {out}")
    print(f"test scenes: {test_scenes}")


# ---------------- Habitat ----------------
def freeze_habitat():
    import pm_habitat
    os.makedirs(SUITE_DIR, exist_ok=True)
    out = os.path.join(SUITE_DIR, f"epm_v{VERSION}_habitat.jsonl")
    n, skipped = 0, 0
    with open(out, "w") as f:
        for split, scene, seeds, delays in [
                ("dev", HAB_DEV_SCENE, THOR_DEV_SEEDS, HAB_DEV_DELAYS),
                ("test", HAB_TEST_SCENE, THOR_TEST_SEEDS, HAB_TEST_DELAYS)]:
            env = pm_habitat.HabitatPMEnv(scene)
            try:
                for seed in seeds:
                    for delay in delays:
                        base = pm_habitat.build_spec(env, seed, delay=delay,
                                                     cancel=None)
                        if base is None:
                            skipped += len(VARIANTS)
                            continue
                        for variant in VARIANTS:
                            spec = dict(base)
                            c = CANCEL_OF[variant]
                            spec["cancel_step"] = (
                                None if c is None else
                                max(2, delay - 4) if c == "early" else delay + 4)
                            spec["has_intention"] = variant != "control"
                            f.write(json.dumps(
                                line("habitat", split, scene, seed, delay, 1,
                                     variant, spec), sort_keys=True) + "\n")
                            n += 1
            finally:
                env.sim.close()
    print(f"habitat: wrote {n} episodes ({skipped} skipped) -> {out}")


# ---------------- validation (offline) ----------------
def validate():
    problems = []
    counts = {}
    files = [p for p in (os.path.join(SUITE_DIR, f"epm_v{VERSION}_thor.jsonl"),
                         os.path.join(SUITE_DIR, f"epm_v{VERSION}_habitat.jsonl"))
             if os.path.exists(p)]
    if not files:
        raise SystemExit("no suite files to validate")
    twin_seen = {}
    for path in files:
        for i, raw in enumerate(open(path)):
            r = json.loads(raw)
            key = (r["engine"], r["split"], r["scene"], r["delay"], r["load"])
            counts[key] = counts.get(key, 0) + 1
            twin_seen.setdefault(r["twin_group"], set()).add(r["variant"])
            spec = r["spec"]
            where = f"{os.path.basename(path)}:{i+1}"
            # cancel ordering
            cs = (spec.get("cancel_step") if r["engine"] == "habitat"
                  else (spec["intentions"][0].get("cancel_step")
                        if spec.get("intentions") else None))
            ev = (spec.get("event_step") if r["engine"] == "habitat"
                  else spec["intentions"][0]["event_step"]
                  if spec.get("intentions") else None)
            if r["variant"] == "cancel_early" and not (cs and ev and cs < ev):
                problems.append(f"{where}: early cancel not before event")
            if r["variant"] == "cancel_late" and not (cs and ev and cs > ev):
                problems.append(f"{where}: late cancel not after event")
            if r["variant"] in ("control", "live") and cs is not None:
                problems.append(f"{where}: {r['variant']} has cancel_step")
            if r["engine"] == "thor":
                if r["variant"] != "control" and \
                        len(spec.get("intentions", [])) != r["load"]:
                    problems.append(f"{where}: load mismatch")
                if r["variant"] == "control" and "notice" in spec["briefing"]:
                    problems.append(f"{where}: control briefing leaks intention")
                if not spec.get("chores"):
                    problems.append(f"{where}: no chores")
            else:
                for k in ("start", "waypoints", "marker"):
                    if spec.get(k) is None:
                        problems.append(f"{where}: missing {k}")
    incomplete = {g: v for g, v in twin_seen.items() if len(v) != 4}
    for g, v in list(incomplete.items())[:5]:
        problems.append(f"twin group {g} incomplete: {sorted(v)}")
    manifest = {
        "suite": f"epm_v{VERSION}",
        "files": {os.path.basename(p): {
            "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest(),
            "episodes": sum(1 for _ in open(p))} for p in files},
        "twin_groups": len(twin_seen),
        "incomplete_twin_groups": len(incomplete),
        "cells": {"|".join(map(str, k)): v for k, v in sorted(counts.items())},
        "design": {
            "variants": VARIANTS,
            "thor": {"dev_scene": THOR_DEV_SCENE,
                     "dev_delays": THOR_DEV_DELAYS,
                     "dev_loads": THOR_DEV_LOADS,
                     "dev_seeds": [0, 99], "test_seeds": [100, 199]},
            "habitat": {"dev_scene": HAB_DEV_SCENE,
                        "test_scene": HAB_TEST_SCENE,
                        "dev_delays": HAB_DEV_DELAYS,
                        "load_limitation":
                            "habitat tier is single-intention in v0.1"},
        },
    }
    with open(os.path.join(SUITE_DIR, "MANIFEST.json"), "w") as f:
        json.dump(manifest, f, indent=1, sort_keys=True)
    print(f"validated {sum(m['episodes'] for m in manifest['files'].values())} "
          f"episodes in {len(files)} files; {len(twin_seen)} twin groups; "
          f"{len(problems)} problems")
    for p in problems[:20]:
        print("PROBLEM:", p)
    if problems:
        sys.exit(1)
    print("MANIFEST.json written")


# ---------------- sampled oracle audit ----------------
def audit_thor(n):
    import agents
    from env import ThorPMEnv
    path = os.path.join(SUITE_DIR, f"epm_v{VERSION}_thor.jsonl")
    eps = [json.loads(x) for x in open(path)]
    live = [e for e in eps if e["variant"] == "live" and e["load"] == 1
            and e["delay"] == 6]
    by_scene = {}
    for e in live:
        by_scene.setdefault(e["scene"], []).append(e)
    envh = ThorPMEnv(size=128)
    bad = 0
    try:
        for sc, group in sorted(by_scene.items()):
            for e in group[:n]:
                spec = e["spec"]
                spec["chores"] = [tuple(c) for c in spec["chores"]]
                envh.reset(spec, scene=sc)
                agents.run_oracle(envh, spec)
                adj = envh.adjudicate()
                ok = adj["executed"]
                bad += (not ok)
                print(f"audit {sc} s{e['seed']}: executed={ok}", flush=True)
    finally:
        envh.stop()
    print(f"THOR AUDIT: {bad} failures")
    sys.exit(1 if bad else 0)


def audit_habitat(n):
    import pm_habitat
    import numpy as np
    path = os.path.join(SUITE_DIR, f"epm_v{VERSION}_habitat.jsonl")
    eps = [json.loads(x) for x in open(path)]
    live = [e for e in eps if e["variant"] == "live"]
    by_scene = {}
    for e in live:
        by_scene.setdefault(e["scene"], []).append(e)
    bad = 0
    for sc, group in sorted(by_scene.items()):
        env = pm_habitat.HabitatPMEnv(sc)
        try:
            for e in group[:n]:
                spec = {k: (np.array(v, dtype=np.float32)
                            if k in ("start", "marker", "hot_anchor")
                            else [np.array(p, dtype=np.float32) for p in v]
                            if k in ("waypoints", "lookouts") else v)
                        for k, v in e["spec"].items()}
                pm_habitat.run_policy(env, spec, "oracle")
                ok = bool(env.adjudicate()["executed"])
                bad += (not ok)
                print(f"audit {sc} s{e['seed']}: executed={ok}", flush=True)
        finally:
            env.sim.close()
    print(f"HABITAT AUDIT: {bad} failures")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["freeze-thor", "freeze-habitat", "validate",
                                    "audit-thor", "audit-habitat"])
    ap.add_argument("--n", type=int, default=5)
    a = ap.parse_args()
    if a.cmd == "freeze-thor":
        freeze_thor()
    elif a.cmd == "freeze-habitat":
        freeze_habitat()
    elif a.cmd == "validate":
        validate()
    elif a.cmd == "audit-thor":
        audit_thor(a.n)
    elif a.cmd == "audit-habitat":
        audit_habitat(a.n)
