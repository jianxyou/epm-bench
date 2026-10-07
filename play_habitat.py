#!/usr/bin/env python
"""habitat-sim playground. Run INSIDE the conda env:
  source ~/miniforge3-x86/bin/activate && conda activate habitat
  python play_habitat.py
Each step saves playground_hab.png (the agent's egocentric view).

Commands:
  where            agent position + can it see the marker?
  spawn            (event engine demo) spawn the red marker somewhere far
  goal marker      set navigation goal to the marker
  goal random      set goal to a random navigable point
  go [n]           advance n steps (default 5) along the current path
  quit
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pm_habitat

env = pm_habitat.HabitatPMEnv("apartment_1", res=512)  # hi-res for playing; experiments keep 64
spec = pm_habitat.build_spec(env, seed=0, delay=9999)
env.reset(spec)
print(__doc__)
print("apartment loaded. try: spawn / goal marker / go 20 / where")

_viewer = {"im": None}

def snap():
    try:
        obs = env.sim.get_sensor_observations()
        frame = obs["rgb"][:, :, :3]
        from PIL import Image
        Image.fromarray(frame).save("playground_hab.png")
        import matplotlib
        matplotlib.use("MacOSX")
        import matplotlib.pyplot as plt
        if _viewer["im"] is None:
            plt.ion()
            fig, ax = plt.subplots(num="agent view (habitat)", figsize=(5, 5))
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
        cmd = input("hab> ").strip().split()
    except (EOFError, KeyboardInterrupt):
        break
    if not cmd:
        continue
    op = cmd[0].lower()
    if op == "quit":
        break
    elif op == "where":
        p = env.pos()
        vis = env.visible(env.marker) if env.marker is not None else None
        print(f"position: ({p[0]:.1f}, {p[2]:.1f})  marker spawned: "
              f"{env.marker is not None}  visible: {vis}")
    elif op == "spawn":
        env.marker = np.array(spec["marker"], dtype=np.float32)
        print("(a red beacon just appeared somewhere in the apartment -- "
              "you did NOT see where. try: goal marker; go 30)")
    elif op == "goal" and len(cmd) > 1:
        if cmd[1] == "marker" and env.marker is not None:
            env.set_goal(env.marker); print("goal = marker")
        else:
            env.set_goal(np.array(env.pf.get_random_navigable_point()))
            print("goal = random point")
    elif op == "go":
        n = int(cmd[1]) if len(cmd) > 1 else 5
        for _ in range(n):
            done = env.step_nav()
            env.tick("play")
            if done:
                print(f"arrived at step {env.t}")
                break
        p = env.pos()
        vis = env.visible(env.marker) if env.marker is not None else None
        print(f"t={env.t} position=({p[0]:.1f},{p[2]:.1f}) marker visible: {vis}")
    else:
        print("unknown command; see header")
    snap()
env.sim.close()
