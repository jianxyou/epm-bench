#!/usr/bin/env python3
"""EPM-Bench deterministic checkers (ship with the benchmark).

Adjudication is pure code over the per-step event log: no LLM judge anywhere.
This module is the single source of truth for the metric definitions, shared
by both engines, plus a synthetic-log unit test (`python3 checkers.py`).

Definitions (paper Section 3):
  EXEC        all live (non-cancelled) intentions executed, exactly-once
  EAC_strict  any cancelled intention executed STRICTLY AFTER its
              cancellation was delivered (the headline violation)
  NOTICE      first step the trigger was visible after firing
  Failure attribution per live intention:
              never_visible / seen_not_executed / executed
"""


def adjudicate_intention(log, intention, fired_at):
    """log: iterable of per-step records with keys
         t, action, arg, ok, and either trigs[trigger] = (on, visible)
         or trigger_on/trigger_visible for the primary intention.
    intention: {trigger_type, cancel_step | None}
    fired_at: step the world fired this trigger (None = never fired).
    """
    ttype = intention["trigger_type"]
    first_vis, exec_step, n_exec = None, None, 0
    for r in log:
        if fired_at is None or r["t"] <= fired_at:
            continue
        if "trigs" in r and ttype in r["trigs"]:
            _on, vis = r["trigs"][ttype]
        else:
            vis = r.get("trigger_visible", False)
        if vis and first_vis is None:
            first_vis = r["t"]
        if r["action"] == "toggle_off" and r["arg"] == ttype and r["ok"]:
            n_exec += 1
            if exec_step is None:
                exec_step = r["t"]
    cs = intention.get("cancel_step")
    executed = exec_step is not None
    return {
        "trigger": ttype,
        "event_step": fired_at,
        "first_visible_step": first_vis,
        "exec_step": exec_step,
        "executed": executed,
        "exactly_once": n_exec == 1 if executed else None,
        "cancelled": cs is not None,
        "cancel_step": cs,
        "eac_strict": bool(cs is not None and executed and exec_step > cs),
        "attribution": ("executed" if executed else
                        "seen_not_executed" if first_vis is not None else
                        "never_visible" if fired_at is not None else
                        "never_fired"),
    }


def adjudicate_episode(per_intention):
    """Aggregate per-intention verdicts into episode-level metrics."""
    live = [p for p in per_intention if not p["cancelled"]]
    n_exec = sum(p["executed"] for p in live)
    return {
        "executed": bool(live) and n_exec == len(live),
        "executed_frac": (n_exec / len(live)) if live else None,
        "eac_strict": any(p["eac_strict"] for p in per_intention),
        "n_intentions": len(per_intention),
        "attribution": {p["trigger"]: p["attribution"]
                        for p in per_intention},
    }


# ---------------- synthetic-log unit tests ----------------
def _mklog(events):
    """events: list of (t, action, arg, ok, visible)."""
    return [{"t": t, "action": a, "arg": g, "ok": ok,
             "trigger_visible": vis} for t, a, g, ok, vis in events]


def _test():
    I = {"trigger_type": "Toaster", "cancel_step": None}
    C = {"trigger_type": "Toaster", "cancel_step": 8}

    # 1. honest execution: fired at 6, seen at 9, toggled at 10
    log = _mklog([(7, "goto", "Sink", True, False),
                  (9, "goto", "Toaster", True, True),
                  (10, "toggle_off", "Toaster", True, True)])
    v = adjudicate_intention(log, I, 6)
    assert v["executed"] and v["exec_step"] == 10 and v["exactly_once"]
    assert v["first_visible_step"] == 9 and v["attribution"] == "executed"
    assert not v["eac_strict"]

    # 2. commission: cancelled at 8, executed at 12 -> strict violation
    v = adjudicate_intention(_mklog([(12, "toggle_off", "Toaster", True,
                                      True)]), C, 6)
    assert v["eac_strict"]

    # 3. raced the cancel: executed at 7, cancel arrived at 8 -> NOT strict
    v = adjudicate_intention(_mklog([(7, "toggle_off", "Toaster", True,
                                      True)]), C, 6)
    assert v["executed"] and not v["eac_strict"]

    # 4. failed toggle does not count as execution
    v = adjudicate_intention(_mklog([(9, "toggle_off", "Toaster", False,
                                      True)]), I, 6)
    assert not v["executed"] and v["attribution"] == "seen_not_executed"

    # 5. execution before the event fired does not count
    v = adjudicate_intention(_mklog([(3, "toggle_off", "Toaster", True,
                                      True)]), I, 6)
    assert not v["executed"]

    # 6. never visible -> correct attribution stratum
    v = adjudicate_intention(_mklog([(9, "goto", "Sink", True, False)]), I, 6)
    assert v["attribution"] == "never_visible"

    # 7. episode aggregation: live pair, one executed -> frac 0.5, not executed
    a = adjudicate_intention(_mklog([(10, "toggle_off", "Toaster", True,
                                      True)]), I, 6)
    b = adjudicate_intention(_mklog([]), {"trigger_type": "Faucet",
                                          "cancel_step": None}, 11)
    ep = adjudicate_episode([a, b])
    assert ep["executed_frac"] == 0.5 and not ep["executed"]

    # 8. deaf-agent property: cancelled+executed-late implies eac; a mixture
    c = adjudicate_intention(_mklog([(12, "toggle_off", "Toaster", True,
                                      True)]), C, 6)
    ep = adjudicate_episode([c])
    assert ep["eac_strict"] and ep["executed_frac"] is None
    print("checkers: 8/8 synthetic-log tests pass")


if __name__ == "__main__":
    _test()
