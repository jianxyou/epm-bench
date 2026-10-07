#!/usr/bin/env python
"""Drive the RAW habitat-sim agent yourself -- no benchmark, no wrapper.

Run with the habitat environment's python:
  cd ~/Desktop/my_project/embodied_pm
  ~/miniforge3-x86/envs/habitat/bin/python play_habitat_raw.py
  ~/miniforge3-x86/envs/habitat/bin/python play_habitat_raw.py --scene skokloster-castle

Keys (type, then Enter):
  w  move_forward (0.25 m)      a  turn_left (10 deg)     d  turn_right (10 deg)
  i  look_up                    k  look_down
  w5 / a9 ...  repeat an action n times
  t  teleport to a random navigable point
  p  shortest path from here to a random point (prints its length)
  q  quit
A window shows RGB (left) and depth (right). After every action the script
prints exactly what habitat-sim returns: whether you collided, position,
heading, and whether the floor under you is navigable.
"""
import argparse, math, os
import numpy as np
import habitat_sim

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--scene", default="apartment_1",
                choices=["apartment_1", "skokloster-castle", "van-gogh-room"])
ap.add_argument("--res", type=int, default=384)
args = ap.parse_args()

# ---- 1. simulator config: scene + physics off ----
sim_cfg = habitat_sim.SimulatorConfiguration()
sim_cfg.scene_id = os.path.join(HERE, "data/scene_datasets/habitat-test-scenes", args.scene + ".glb")
sim_cfg.enable_physics = False

# ---- 2. agent config: sensors + the native action space ----
def cam(uuid, kind):
    s = habitat_sim.CameraSensorSpec()
    s.uuid, s.sensor_type = uuid, kind
    s.resolution = [args.res, args.res]
    s.position = [0.0, 1.5, 0.0]            # camera 1.5 m above the floor
    return s

agent_cfg = habitat_sim.agent.AgentConfiguration()
agent_cfg.sensor_specifications = [cam("rgb", habitat_sim.SensorType.COLOR),
                                   cam("depth", habitat_sim.SensorType.DEPTH)]
A = habitat_sim.agent.ActionSpec
M = habitat_sim.agent.ActuationSpec
agent_cfg.action_space = {
    "move_forward": A("move_forward", M(amount=0.25)),
    "turn_left":    A("turn_left",    M(amount=10.0)),
    "turn_right":   A("turn_right",   M(amount=10.0)),
    "look_up":      A("look_up",      M(amount=10.0)),
    "look_down":    A("look_down",    M(amount=10.0)),
}
sim = habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [agent_cfg]))
agent = sim.initialize_agent(0)
pf = sim.pathfinder
st = agent.get_state(); st.position = pf.get_random_navigable_point(); agent.set_state(st)

KEYS = {"w": "move_forward", "a": "turn_left", "d": "turn_right", "i": "look_up", "k": "look_down"}

def heading_deg(q):
    # yaw of the agent's forward axis (-Z), in degrees
    v = q * np.quaternion(0, 0, 0, -1) * q.conjugate()
    return math.degrees(math.atan2(-v.x, -v.z)) % 360

_view = {}
def show(obs):
    try:
        import matplotlib; matplotlib.use("MacOSX")
        import matplotlib.pyplot as plt
        rgb, dep = obs["rgb"][:, :, :3], obs["depth"]
        if not _view:
            plt.ion()
            fig, (a, b) = plt.subplots(1, 2, num="habitat-sim, raw", figsize=(9, 4.6))
            for ax in (a, b): ax.axis("off")
            _view["rgb"] = a.imshow(rgb); a.set_title("rgb sensor")
            _view["dep"] = b.imshow(dep, cmap="viridis", vmin=0, vmax=6); b.set_title("depth sensor (m)")
        else:
            _view["rgb"].set_data(rgb); _view["dep"].set_data(dep)
        plt.pause(0.05)
    except Exception as ex:
        print(f"(viewer unavailable: {type(ex).__name__})")

def report(tag, obs, collided=None):
    s = agent.get_state()
    p = s.position
    print(f"{tag:<22} collided={collided}  pos=({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})  "
          f"heading={heading_deg(s.rotation):5.1f} deg  navigable={pf.is_navigable(p)}")
    show(obs)

print(__doc__)
print("scene:", args.scene, "| native actions:", list(agent_cfg.action_space))
print("navmesh area (m^2):", round(pf.navigable_area, 1))
report("start", sim.get_sensor_observations())

while True:
    try:
        cmd = input("> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        break
    if not cmd:
        continue
    if cmd == "q":
        break
    if cmd == "t":
        st = agent.get_state(); st.position = pf.get_random_navigable_point(); agent.set_state(st)
        report("teleport (set_state)", sim.get_sensor_observations()); continue
    if cmd == "p":
        path = habitat_sim.ShortestPath()
        path.requested_start = agent.get_state().position
        path.requested_end = pf.get_random_navigable_point()
        ok = pf.find_path(path)
        print(f"find_path -> {ok}, geodesic distance {path.geodesic_distance:.2f} m, {len(path.points)} waypoints")
        continue
    key, n = cmd[0], int(cmd[1:]) if cmd[1:].isdigit() else 1
    if key not in KEYS:
        print("keys: w a d i k (optionally + count), t, p, q"); continue
    for _ in range(n):
        obs = sim.step(KEYS[key])          # <-- the whole native interface
    report(f"sim.step('{KEYS[key]}')", obs, obs.get("collided"))

sim.close()
