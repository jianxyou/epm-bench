"""Episode specs: foreground chores + one deferred intention + event schedule.

All seeded. The chore list is the *distraction* (FindingDory-style pick&place);
the intention is PM-Bench-style: announced at step 0, trigger fires later.
"""
import random

# FloorPlan1 kitchen furniture we rely on (verified in smoke test)
CHORE_MOVES = [
    ("Apple", "Fridge"), ("Tomato", "Fridge"), ("Bread", "Fridge"),
    ("Mug", "CoffeeMachine"), ("Cup", "Sink"), ("Potato", "Microwave"),
    ("Egg", "Bowl"), ("Lettuce", "Fridge"),
]
TRIGGERS = ["Toaster", "Faucet", "Microwave", "CoffeeMachine"]


def build_episode_for_scene(types, seed=0, delay=6, cancel=None, n_chores=6,
                            trigger=None, n_intentions=1):
    """Restricted to object types present in the scene (types from
    env.scan_types()). n_intentions > 1 stacks additional deferred intentions on
    other togglable objects, events staggered by 5 steps. `cancel` applies to the
    FIRST intention only (selective-revocation design)."""
    rng = random.Random(seed)
    avail_moves = [(a, b) for a, b in CHORE_MOVES
                   if a in types["pickupable"] and b in types["receptacle"]]
    avail_trig = [t for t in TRIGGERS if t in types["toggleable"]]
    if not avail_moves or len(avail_trig) < n_intentions:
        return None
    n = min(n_chores, len(avail_moves))
    moves = rng.sample(avail_moves, n)
    if trigger in avail_trig:
        rest = [t for t in avail_trig if t != trigger]
        trigs = [trigger] + rng.sample(rest, n_intentions - 1)
    else:
        trigs = rng.sample(avail_trig, n_intentions)
    cancel_step = None
    if cancel == "early":
        cancel_step = max(2, delay - 3)
    elif cancel == "late":
        cancel_step = delay + 2
    intentions = []
    for i, tg in enumerate(trigs):
        intentions.append({
            "trigger_type": tg,
            "instruction": (f"If you ever notice the {tg} is ON, turn it off. "
                            f"Right now it is off."),
            "event_step": delay + 5 * i,
            "cancel_step": cancel_step if i == 0 else None,
        })
    briefing = ("Your chores, in order: "
                + "; ".join(f"put the {a} into the {b}" for a, b in moves)
                + ". While you work: "
                + " ".join(it["instruction"] for it in intentions))
    return {"seed": seed, "chores": moves, "intention": intentions[0],
            "intentions": intentions, "briefing": briefing}


def build_episode(seed=0, delay=6, cancel=None, n_chores=6, trigger=None):
    """cancel: None | 'early' | 'late'.
    delay: event fires after this many agent steps.
    Layout: chores take ~3 steps each (goto+pickup, goto+put), so an episode is
    ~20-30 steps; event at step `delay` lands mid-chores."""
    rng = random.Random(seed)
    moves = rng.sample(CHORE_MOVES, n_chores)
    trig = trigger or rng.choice(TRIGGERS)
    event_step = delay
    cancel_step = None
    if cancel == "early":
        cancel_step = max(2, event_step - 3)   # before the world changes
    elif cancel == "late":
        cancel_step = event_step + 2           # after it fired, before/near noticing
    intention = {
        "trigger_type": trig,
        "instruction": (f"While you work: if you ever notice the {trig} is ON, "
                        f"turn it off. Right now it is off."),
        "event_step": event_step,
        "cancel_step": cancel_step,
    }
    briefing = ("Your chores, in order: "
                + "; ".join(f"put the {a} into the {b}" for a, b in moves)
                + ". " + intention["instruction"])
    return {
        "seed": seed, "chores": moves, "intention": intention,
        "briefing": briefing,
    }
