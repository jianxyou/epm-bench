#!/usr/bin/env python3
"""Scheduling-geometry study (mock actor, zero API).

Question: under intention load n and injection policy P, what are the MECHANICAL
floors/ceilings of the cost-execution-cancellation trade-off, before any LLM
attention effects? A rule actor has no attention limit, so whatever it loses is
pure information starvation (note not present at the decisive moment); whatever
the real LLM loses beyond that is attention tax.

Policies (what the store injects each step):
  bank   - every live+dead note, every step (naive store; cost n/step)
  every5 - all notes every 5th step (sparse; cost n/5 per step)
  rr     - round-robin, one note per step (cost 1/step)
  rrn    - rr + cancel handling: on cancellation, strike note from rotation and
           inject a one-time CANCELLED notice (mechanical sched policy)
  sight  - a note only when its trigger is visible this step

Mock actor: window-bounded reader. Acts on intention I iff trigger visible-ON
AND (briefing still in window OR I's note injected this step) AND not believed
cancelled (cancel message in window, or struck in rrn). One semantic action/step.

CSV row per episode: policy, load, cancel, seed, executed_frac, eac_strict,
notes_injected, chores_done, steps_total.
"""
import argparse
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tasks
from env import ThorPMEnv

OUT_DEFAULT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "results", "sched_geometry.csv")
FIELDS = ["ts", "policy", "load", "cancel", "seed", "executed_frac",
          "eac_strict", "n_exec_dead", "notes_injected", "chores_done",
          "steps_total", "window", "delay"]


def notes_for(policy, t, intents, struck, visible_types, rr_ptr):
    """Return (list of intention idxs whose note is injected this step,
    one-time notices, new rr_ptr)."""
    live = [i for i in range(len(intents)) if i not in struck]
    if policy == "bank":
        return list(range(len(intents))), [], rr_ptr
    if policy == "every5":
        return (list(range(len(intents))) if t % 5 == 0 else []), [], rr_ptr
    if policy in ("rr", "rrn"):
        pool = live if policy == "rrn" else list(range(len(intents)))
        if not pool:
            return [], [], rr_ptr
        idx = pool[rr_ptr % len(pool)]
        return [idx], [], rr_ptr + 1
    if policy == "sight":
        return [i for i, it in enumerate(intents)
                if it["trigger_type"] in visible_types], [], rr_ptr
    raise SystemExit(f"unknown policy {policy}")


def run_episode(envh, spec, policy, window=6, max_steps=40, grade_dump=None,
                grade_meta=None):
    intents = spec.get("intentions") or [spec["intention"]]
    transcript = []
    struck = set()          # rrn: cancelled intentions removed from rotation
    pending_notice = []     # rrn: one-time cancel notices to inject
    notes_injected = 0
    rr_ptr = 0
    todo = []
    for a, b in spec["chores"]:
        todo += [("goto", a), ("pickup", a), ("goto", b), ("put", b)]
    i = 0
    while envh.t < max_steps:
        msgs = envh.pending_messages()
        obs = envh.observe()
        line = obs
        if envh.t == 0:
            line = f"BRIEFING: {spec['briefing']} | " + line
        if msgs:
            line = " | ".join(msgs) + " | " + line
            if policy == "rrn":
                for k, it in enumerate(intents):
                    if any(it["trigger_type"].lower() in m.lower()
                           for m in msgs):
                        struck.add(k)
                        pending_notice.append(k)
        transcript.append(line)
        win = transcript[-window:]
        visible_types = {it["trigger_type"] for it in intents
                         if f"{it['trigger_type']} (ON)" in obs
                         or f"{it['trigger_type']} (off)" in obs}
        inj, _, rr_ptr = notes_for(policy, envh.t, intents, struck,
                                   visible_types, rr_ptr)
        notes = {k: f"[STORE] {intents[k]['instruction']}" for k in inj}
        notices = {k: f"[STORE] the {intents[k]['trigger_type']} intention is "
                      f"CANCELLED, ignore it." for k in pending_notice}
        pending_notice = []
        final_notes, final_notices = notes, notices  # last step's injections
        notes_injected += len(notes) + len(notices)
        blob = " || ".join(win)
        acted = False
        for k, it in enumerate(intents):
            trig = it["trigger_type"]
            has_intent = (("BRIEFING" in blob and trig in blob)
                          or k in notes)
            believes_cancelled = (
                k in notices
                or (policy == "rrn" and k in struck)
                or any(trig.lower() in ln.lower() and "never mind" in ln
                       for ln in win))
            sees_on = f"{trig} (ON)" in obs
            already = any(r["action"] == "toggle_off" and r["arg"] == trig
                          and r["ok"] for r in envh.log)
            if sees_on and has_intent and not believes_cancelled \
                    and not already:
                envh.act("toggle_off", trig)
                acted = True
                break
        if acted:
            continue
        if i < len(todo):
            a, arg = todo[i]; i += 1
            envh.act(a, arg)
        else:
            envh.act("wait")
    adj = envh.adjudicate()
    dead_exec = sum(1 for p in adj["per_intention"]
                    if p["cancelled"] and p["executed"])
    chores = sum(1 for r in envh.log if r["action"] == "put" and r["ok"])
    if grade_dump is not None:
        # Three grading regimes over the SAME finished episode.
        # world-state: the simulator log (ground truth adjudication).
        # QA-style: quiz the agent's accessible text at episode end -- exactly
        #   what a dialogue/QA benchmark can observe.
        # selection-style: ask "would you act on X now?" at episode end -- the
        #   menu-probe a selection benchmark scores.
        import json as _json
        win_end = transcript[-window:]
        blob_end = " || ".join(win_end)
        recs = []
        for k, it in enumerate(intents):
            trig = it["trigger_type"]
            per = adj["per_intention"][k]
            # end-of-episode probes receive EXACTLY the actor's information
            # at the final step: window text plus that step's injected notes
            qa_knows_intent = (("BRIEFING" in blob_end and trig in blob_end)
                               or k in final_notes)
            qa_knows_cancel = (
                k in final_notices
                or (policy == "rrn" and k in struck)
                or any(trig.lower() in ln.lower() and "never mind" in ln
                       for ln in win_end))
            sel_would_act = qa_knows_intent and not qa_knows_cancel
            recs.append({
                **(grade_meta or {}), "intent_idx": k, "trigger": trig,
                "cancelled": per["cancelled"],
                "world_executed": per["executed"],
                "world_eac": per["eac_strict"],
                "qa_knows_intent_end": qa_knows_intent,
                "qa_knows_cancel_end": qa_knows_cancel,
                "sel_would_act_end": sel_would_act,
            })
        with open(grade_dump, "a") as gf:
            for r in recs:
                gf.write(_json.dumps(r) + "\n")
    return {"executed_frac": adj["executed_frac"],
            "eac_strict": adj["eac_strict"], "n_exec_dead": dead_exec,
            "notes_injected": notes_injected, "chores_done": chores,
            "steps_total": adj["steps_total"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policies", default="bank,every5,rr,rrn,sight")
    ap.add_argument("--loads", default="1,2,3")
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--cancel-arms", default="none,late")
    ap.add_argument("--window", type=int, default=6)
    ap.add_argument("--delay", type=int, default=6)
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--grade-dump", default=None,
                    help="append per-intention three-regime grading records "
                         "(world/QA/selection) to this JSONL")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    new = not os.path.exists(args.out)
    envh = ThorPMEnv(size=128)
    n_done = 0
    try:
        with open(args.out, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            if new:
                w.writeheader()
            for load in [int(x) for x in args.loads.split(",")]:
                for cancel in args.cancel_arms.split(","):
                    canc = None if cancel == "none" else cancel
                    for pol in args.policies.split(","):
                        for s in range(args.seeds):
                            for attempt in (1, 2):
                                try:
                                    types = envh.scan_types("FloorPlan1")
                                    spec = tasks.build_episode_for_scene(
                                        types, seed=s, delay=args.delay,
                                        cancel=canc, n_intentions=load)
                                    if spec is None:
                                        r = None
                                        break
                                    envh.reset(spec, scene="FloorPlan1")
                                    r = run_episode(
                                        envh, spec, pol, window=args.window,
                                        grade_dump=args.grade_dump,
                                        grade_meta={"policy": pol,
                                                    "load": load,
                                                    "cancel": cancel,
                                                    "seed": s,
                                                    "window": args.window,
                                                    "delay": args.delay})
                                    break
                                except Exception as e:
                                    print(f"ep load{load} {pol} s{s} "
                                          f"attempt{attempt}: "
                                          f"{type(e).__name__} {str(e)[:80]}",
                                          flush=True)
                                    try:
                                        envh.stop()
                                    except Exception:
                                        pass
                                    envh = ThorPMEnv(size=128)
                                    r = None
                            if r is None:
                                continue
                            w.writerow({"ts": int(time.time()), "policy": pol,
                                        "load": load, "cancel": cancel,
                                        "seed": s, "window": args.window,
                                        "delay": args.delay, **r})
                            f.flush()
                            n_done += 1
                        print(f"cell done: load={load} cancel={cancel} "
                              f"pol={pol} (total {n_done})", flush=True)
    finally:
        envh.stop()
        print(f"TOTAL {n_done} episodes -> {args.out}")


if __name__ == "__main__":
    main()
