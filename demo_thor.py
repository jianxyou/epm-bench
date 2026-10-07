#!/usr/bin/env python3
"""Live demo of one EPM-Bench episode in AI2-THOR.

  python3 demo_thor.py                              # seed 8, cancel-early, raw store (bank), LLM actor
  python3 demo_thor.py --mem sched2                 # same episode, status-tracked store
  python3 demo_thor.py --actor human                # you are the actor: type the action each step
  python3 demo_thor.py --auto 1.5                   # no Enter, 1.5 s per step

A window shows the agent's first-person view. The terminal shows, at every step, exactly what the
actor receives (memory injection + user message + last result + observation) and what it replies.
In LLM mode press Enter to advance one step. In human mode type one of:
  goto X | pickup X | put X | toggle_on X | toggle_off X | look_around | wait | done | q
At the end the episode is graded from world state, exactly as in the paper.
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agents
from env import ThorPMEnv

ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=8)
ap.add_argument("--variant", default="cancel_early", choices=["control", "live", "cancel_early", "cancel_late"])
ap.add_argument("--mem", default="bank", choices=["none", "bank", "retr", "summ", "sched2", "sched1e", "retr2", "rwim4", "rwim5"])
ap.add_argument("--actor", default="llm", choices=["llm", "human"])
ap.add_argument("--model", default="openai/gpt-4o-mini")
ap.add_argument("--delay", type=int, default=6)
ap.add_argument("--auto", type=float, default=None, help="seconds per step instead of Enter (LLM mode)")
ap.add_argument("--headless", action="store_true")
args = ap.parse_args()

HERE = os.path.dirname(os.path.abspath(__file__))
spec = None
for raw in open(os.path.join(HERE, "suite", "epm_v0.1_thor.jsonl")):
    e = json.loads(raw)
    if (e["scene"] == "FloorPlan1" and e["seed"] == args.seed and e["delay"] == args.delay
            and e["load"] == 1 and e["variant"] == args.variant):
        spec = dict(e["spec"]); spec["chores"] = [tuple(c) for c in spec["chores"]]
        if args.variant == "control":
            spec["has_intention"] = False
        break
if spec is None:
    raise SystemExit("no such episode in the frozen suite")
it = spec["intention"]
print(__doc__)
print(f"Episode: seed {args.seed}, {args.variant}, memory = {args.mem}, actor = {args.actor}")
print(f"Script : trigger {it['trigger_type']} switched ON at step {it['event_step']} (out of view); "
      f"cancel at step {it.get('cancel_step')}\n")

env = ThorPMEnv(size=480)
_view = {}


def show(title):
    if args.headless:
        return
    try:
        import matplotlib; matplotlib.use("MacOSX")
        import matplotlib.pyplot as plt
        frame = env.c.last_event.frame
        if not _view:
            plt.ion()
            fig, ax = plt.subplots(num="what the agent sees (AI2-THOR)", figsize=(6.4, 4.8))
            ax.axis("off"); _view["ax"] = ax; _view["im"] = ax.imshow(frame)
        else:
            _view["im"].set_data(frame)
        _view["ax"].set_title(title, loc="left", fontsize=10)
        plt.pause(0.05)
    except Exception as ex:
        print(f"(viewer unavailable: {type(ex).__name__})")


# ---- intercept the actor call: print what it sees, get the reply (LLM or human) ----
_orig_call = agents._call
BAR = "-" * 78


def demo_call(client, model, system, messages, max_tokens):
    if system is not agents.ACTOR_SYSTEM:            # bookkeeper / summariser calls pass through
        return _orig_call(client, model, system, messages, max_tokens)
    last = messages[-1]["content"]
    if isinstance(last, list):                         # vision tier
        last = next(b["text"] for b in last if b.get("type") == "text")
    show(f"step {env.t}")
    print(f"\n{BAR}\nSTEP {env.t}  |  the actor receives:\n{BAR}\n{last}\n{BAR}")
    if args.actor == "human":
        while True:
            try:
                raw = input("your action > ").strip()
            except (EOFError, KeyboardInterrupt):
                raise SystemExit("\nbye")
            if raw == "q":
                raise SystemExit("bye")
            parts = raw.split(None, 1)
            if parts and parts[0] in ("goto", "pickup", "put", "toggle_on", "toggle_off", "look_around", "wait", "done"):
                arg = parts[1] if len(parts) > 1 else None
                return json.dumps({"action": parts[0], "arg": arg, "why": "human"}), 0
            print("  (goto X | pickup X | put X | toggle_on X | toggle_off X | look_around | wait | done | q)")
    out, u = _orig_call(client, model, system, messages, max_tokens)
    print(f"ACTOR REPLIES: {out.strip()[:300]}")
    if args.auto:
        time.sleep(args.auto)
    else:
        try:
            input("[Enter] next step ")
        except (EOFError, KeyboardInterrupt):
            raise SystemExit("\nbye")
    return out, u


agents._call = demo_call

# ---- make the scripted events visible in the terminal ----
_orig_act = env.act


def act_hook(action, arg=None):
    rec = _orig_act(action, arg)
    print(f"  world: {action} {arg or ''} -> {'OK' if rec['ok'] else 'FAILED'} ({rec['note']})")
    if env.t == it["event_step"]:
        print(f"  *** world switches the {it['trigger_type']} ON (agent elsewhere) ***")
    return rec


env.act = act_hook

try:
    env.reset(spec, scene="FloorPlan1")
    show("step 0")
    info = agents.run_llm(env, spec, mem=args.mem, model=args.model)
    adj = env.adjudicate()
finally:
    env.stop()

print(f"\n{BAR}\nGRADED FROM WORLD STATE\n{BAR}")
print(f"  trigger switched on at step : {adj['event_step']}")
print(f"  first in the agent's view   : {adj['first_visible_step']}")
print(f"  user cancelled at step      : {adj['cancel_step']}")
print(f"  agent switched it off at    : {adj['exec_step']}")
print(f"  EXEC (executed)             : {adj['executed']}")
print(f"  EAC  (executed after cancel): {adj['eac_strict']}")
print(f"  api tokens                  : {info.get('api_tokens')}")
