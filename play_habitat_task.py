#!/usr/bin/env python
"""Play one benchmark episode YOURSELF, sitting in the model's seat.

Run with the habitat environment's python:
  cd ~/Desktop/my_project/embodied_pm
  ~/miniforge3-x86/envs/habitat/bin/python play_habitat_task.py --variant cancel_early --mem bank

Each step you see what the model sees: the first-person view (a window opens),
the text observation, and whatever the chosen memory regime injects. You answer
with one key:
  Enter or c   continue   (keep doing what you are doing)
  i            interrupt  (leave the chores to act on a standing instruction)
  r            resume     (go back to the chores)
  c 5          continue for 5 steps
  q            quit
At the end the episode is graded exactly like the model's episodes.

Options:
  --seed N         which episode (0..99, a few are missing)      default 0
  --variant V      control | live | cancel_early | cancel_late   default cancel_early
  --mem M          none | bank | sched2 | sched1                 default bank
  --headless       no picture window (text only)
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pm_habitat as H

ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--variant", default="cancel_early",
                choices=["control", "live", "cancel_early", "cancel_late"])
ap.add_argument("--mem", default="bank", choices=["none", "bank", "sched2", "sched1"])
ap.add_argument("--delay", type=int, default=10)
ap.add_argument("--headless", action="store_true")
args = ap.parse_args()

spec = None
suite = os.path.join(os.path.dirname(os.path.abspath(__file__)), "suite", "epm_v0.1_habitat.jsonl")
for raw in open(suite):
    e = json.loads(raw)
    if (e["split"] == "dev" and e["delay"] == args.delay and e["seed"] == args.seed
            and e["variant"] == args.variant):
        spec = e["spec"]; break
if spec is None:
    raise SystemExit(f"no episode for seed {args.seed} / {args.variant} (try another seed)")

RES = 512
env = H.HabitatPMEnv("apartment_1", res=RES)
_view = {"im": None, "mk": None, "ax": None}


def _project(p):
    import quaternion
    st = env.sim.get_agent(0).get_state().sensor_states["rgb"]
    R = quaternion.as_rotation_matrix(st.rotation)
    pc = R.T @ (np.asarray(p, dtype=np.float64) - np.asarray(st.position, dtype=np.float64))
    if pc[2] >= -0.05:
        return None
    f = RES / 2.0
    return (RES / 2 + f * pc[0] / (-pc[2]), RES / 2 - f * pc[1] / (-pc[2]))


def show_frame():
    if args.headless:
        return
    try:
        import matplotlib
        matplotlib.use("MacOSX")
        import matplotlib.pyplot as plt
        frame = env.sim.get_sensor_observations()["rgb"][:, :, :3]
        if _view["im"] is None:
            plt.ion()
            fig, ax = plt.subplots(num="what the agent sees (habitat)", figsize=(6, 6))
            ax.axis("off")
            _view["ax"] = ax
            _view["im"] = ax.imshow(frame)
        else:
            _view["im"].set_data(frame)
        for art in (_view["mk"] or []):
            art.remove()
        _view["mk"] = []
        if env.marker is not None and env.visible(env.marker):
            b = _project(env.marker)
            t = _project(np.asarray(env.marker) + np.array([0, 0.9, 0]))
            if b and t:
                _view["mk"] += _view["ax"].plot([b[0], t[0]], [b[1], t[1]], color="#d03b3b", linewidth=5)
                _view["mk"].append(_view["ax"].scatter([t[0]], [t[1]], s=160, color="#d03b3b",
                                                       edgecolors="white", linewidths=1.5, zorder=5))
        _view["ax"].set_title(f"step {env.t}", loc="left")
        plt.pause(0.05)
    except Exception as ex:                      # never let the viewer kill the episode
        print(f"(viewer unavailable: {type(ex).__name__})")


class HumanActor:
    tokens = 0
    last_raw = ""
    _skip = 0

    def decide(self, window_texts, note):
        show_frame()
        print("\n" + "-" * 70)
        if note:
            print(f"MEMORY SAYS : {note}")
        print(f"YOU OBSERVE : {window_texts[-1]}")
        if HumanActor._skip > 0:
            HumanActor._skip -= 1
            print("decision    : continue (auto)")
            return "continue"
        while True:
            try:
                raw = input("decision [Enter=continue, i=interrupt, r=resume, q=quit] > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                raise SystemExit("\nbye")
            parts = raw.split()
            if not parts or parts[0] in ("c", "continue"):
                if len(parts) > 1 and parts[1].isdigit():
                    HumanActor._skip = int(parts[1]) - 1
                return "continue"
            if parts[0] in ("i", "interrupt"):
                return "interrupt"
            if parts[0] in ("r", "resume"):
                return "resume"
            if parts[0] in ("q", "quit"):
                raise SystemExit("bye")
            print("  (type Enter, i, r or q)")


print(__doc__)
print(f"Episode: apartment_1, seed {args.seed}, variant = {args.variant}, memory = {args.mem}")
print("Your chores are walked automatically. You only decide, at every step, whether")
print("to keep going, to interrupt them, or to go back to them.\n")
H.MockActor = HumanActor
chores = H.run_llm_tier(env, spec, mem=args.mem, mock=True)
adj = env.adjudicate()
print("\n" + "=" * 70)
print("GRADED FROM WORLD STATE (the same way the models are graded)")
print(f"  beacon appeared at step     : {adj['event_step']}")
print(f"  you first had it in view at : {adj['first_visible_step']}")
print(f"  user cancelled at step      : {adj['cancel_step']}")
print(f"  you pressed it at step      : {adj['exec_step']}")
print(f"  executed                    : {adj['executed']}")
print(f"  VIOLATION (pressed after cancellation): {adj['eac_strict']}")
print(f"  chores finished             : {chores}")
env.sim.close()
