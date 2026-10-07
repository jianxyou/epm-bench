#!/usr/bin/env python3
"""AI2-THOR playground. Run:  python3 play_thor.py
A window opens with the kitchen; type commands here; each step also saves
playground_thor.png so you can watch the agent's view frame by frame.

Commands:
  look                 show what the agent currently sees
  goto <Type>          e.g. goto Fridge / goto Toaster / goto CoffeeMachine
  pickup <Type>        e.g. pickup Tomato
  put <Type>           put held object into e.g. put Fridge
  on <Type> / off <Type>   toggle e.g. on CoffeeMachine
  open <Type> / close <Type>   e.g. open Fridge (must be visible)
  objects              list interactable object types in this scene
  fire                 (event engine demo) force the Toaster ON behind your back
  quit
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tasks
from env import ThorPMEnv

envh = ThorPMEnv(size=320)  # 640 looks nicer but lags on Apple Silicon (Rosetta)
types = envh.scan_types("FloorPlan1")
spec = tasks.build_episode_for_scene(types, seed=0, delay=9999)  # event never fires
envh.reset(spec, scene="FloorPlan1")
print(__doc__)
print("scene ready. interactable types:")
print("  pickupable:", ", ".join(types["pickupable"][:12]), "...")
print("  toggleable:", ", ".join(types["toggleable"]))

CANON = {t.lower(): t for t in (types["pickupable"] + types["receptacle"]
                                 + types["toggleable"])}

def fix(arg):
    """case-insensitive object names: 'fridge' -> 'Fridge'"""
    return CANON.get(arg.lower(), arg) if arg else arg

_viewer = {"im": None}

def snap():
    frame = envh.c.last_event.frame
    try:
        from PIL import Image
        Image.fromarray(frame).save("playground_thor.png")
    except ImportError:
        pass
    # live viewer window (replaces the broken Unity popup on macOS)
    try:
        import matplotlib
        matplotlib.use("MacOSX")
        import matplotlib.pyplot as plt
        if _viewer["im"] is None:
            plt.ion()
            fig, ax = plt.subplots(num="agent view", figsize=(5, 3.8))
            ax.axis("off")
            _viewer["im"] = ax.imshow(frame)
        else:
            _viewer["im"].set_data(frame)
        plt.pause(0.05)
    except Exception:
        pass

snap()
while True:
    try:
        cmd = input("thor> ").strip().split()
    except (EOFError, KeyboardInterrupt):
        break
    if not cmd:
        continue
    op = cmd[0].lower()
    arg = fix(cmd[1]) if len(cmd) > 1 else None
    if op == "quit":
        break
    elif op == "look":
        print(envh.observe())
    elif op == "objects":
        print("toggleable:", types["toggleable"])
        print("receptacles:", types["receptacle"][:15])
    elif op == "fire":
        t = envh.find_type("Toaster")
        envh.c.step(action="ToggleObjectOn", objectId=t["objectId"], forceAction=True)
        print("(the world just turned the Toaster ON -- did you see it? type 'look')")
    elif op in ("goto", "pickup", "put"):
        r = envh.act(op, arg)
        print(("ok: " if r["ok"] else "FAILED: ") + r["note"])
        print(envh.observe())
    elif op in ("on", "off"):
        r = envh.act("toggle_on" if op == "on" else "toggle_off", arg)
        print(("ok: " if r["ok"] else "FAILED: ") + r["note"])
    elif op in ("open", "close") and arg:
        t = envh.find_type(arg)
        if not t:
            print(f"no {arg} found")
        else:
            ev = envh.c.step(action="OpenObject" if op == "open" else "CloseObject", objectId=t["objectId"])
            print(("ok" if ev.metadata["lastActionSuccess"] else "FAILED: " + ev.metadata["errorMessage"][:80]))
    else:
        print("unknown command; see header")
    snap()
envh.stop()
