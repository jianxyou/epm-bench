#!/usr/bin/env python
"""Prospective memory episodes on habitat-sim (multi-room apartment).

World = scene geometry + navmesh. Foreground chores = visiting waypoints.
Deferred intention = "if you ever SEE the marker appear, go stand next to it."
Event engine spawns the marker (a world-state point) at step E, placed out of
the agent's current view. Visibility is geometric: within FOV half-angle, within
vis_dist, and line-of-sight proxy (geodesic/euclid ratio < 1.15). Execution =
agent within 1.5 m of the marker. Cancellation message at step C (late/early).

Run inside the conda 'habitat' env:
  python pm_habitat.py --policy oracle --episodes 5 --out results/habitat.csv
"""
import argparse
import csv
import math
import os
import random
import time

import numpy as np
import habitat_sim
from habitat_sim.utils.common import quat_from_angle_axis

SCENE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "data/scene_datasets/habitat-test-scenes")
STEP_LEN = 0.5          # meters advanced per semantic step
VIS_DIST = 5.0
FOV_HALF = math.radians(45)
EXEC_RADIUS = 0.5
EXEC_STAY = 2
LOS_RATIO = 1.15


def make_sim(scene, res=64):
    path = os.path.join(SCENE_DIR, scene + ".glb")
    cfg = habitat_sim.SimulatorConfiguration()
    cfg.scene_id = path
    agent_cfg = habitat_sim.agent.AgentConfiguration()
    sensor = habitat_sim.CameraSensorSpec()
    sensor.uuid = "rgb"
    sensor.resolution = [res, res]
    agent_cfg.sensor_specifications = [sensor]
    return habitat_sim.Simulator(habitat_sim.Configuration(cfg, [agent_cfg]))


class HabitatPMEnv:
    def __init__(self, scene="apartment_1", res=64):
        self.sim = make_sim(scene, res)
        self.scene = scene
        self.pf = self.sim.pathfinder
        self.agent = self.sim.get_agent(0)

    # ---------- geometry helpers ----------
    def geodesic(self, a, b):
        p = habitat_sim.ShortestPath()
        p.requested_start = np.array(a, dtype=np.float32)
        p.requested_end = np.array(b, dtype=np.float32)
        if not self.pf.find_path(p):
            return None
        return p.geodesic_distance

    def path_points(self, a, b):
        p = habitat_sim.ShortestPath()
        p.requested_start = np.array(a, dtype=np.float32)
        p.requested_end = np.array(b, dtype=np.float32)
        if not self.pf.find_path(p):
            return None
        return [np.array(q) for q in p.points]

    def pos(self):
        return np.array(self.agent.get_state().position)

    def face(self, target):
        d = np.array(target) - self.pos()
        yaw = math.atan2(-d[0], -d[2])
        st = self.agent.get_state()
        st.rotation = quat_from_angle_axis(yaw, np.array([0, 1.0, 0]))
        st.sensor_states = {}
        self.agent.set_state(st, False)

    def teleport(self, p):
        st = self.agent.get_state()
        st.position = np.array(p, dtype=np.float32)
        st.sensor_states = {}
        self.agent.set_state(st, False)

    def visible(self, point):
        """FOV + distance + line-of-sight proxy."""
        d = np.array(point) - self.pos()
        dist = float(np.linalg.norm(d))
        if dist > VIS_DIST or dist < 1e-6:
            return False
        st = self.agent.get_state()
        q = st.rotation
        # agent forward = -Z rotated by q
        fwd = q * np.quaternion(0, 0, 0, -1) * q.conjugate()
        f = np.array([fwd.x, fwd.y, fwd.z])
        cosang = float(np.dot(f, d) / (np.linalg.norm(f) * dist + 1e-9))
        if cosang < math.cos(FOV_HALF):
            return False
        g = self.geodesic(self.pos(), point)
        if g is None or g > dist * LOS_RATIO + 0.3:
            return False
        return True

    # ---------- episode ----------
    def reset(self, spec):
        self.spec = spec
        self.t = 0
        self.log = []
        self.fired_at = None
        self.marker = None
        self.exec_step = None
        self.nav_path = None
        self.nav_i = 0
        self.sim.seed(spec["seed"])
        self.teleport(spec["start"])
        self.face(spec["waypoints"][0])

    def set_goal(self, target):
        self.nav_path = self.path_points(self.pos(), target)
        self.nav_i = 0

    def step_nav(self):
        """Advance STEP_LEN along current path; face movement direction."""
        if not self.nav_path:
            return True
        remaining = STEP_LEN
        pos = self.pos()
        while self.nav_i < len(self.nav_path) - 1 and remaining > 0:
            nxt = self.nav_path[self.nav_i + 1]
            seg = np.linalg.norm(nxt - pos)
            if seg <= remaining + 1e-6:
                remaining -= seg
                pos = nxt
                self.nav_i += 1
            else:
                pos = pos + (nxt - pos) / seg * remaining
                remaining = 0
        heading_target = (self.nav_path[self.nav_i + 1]
                          if self.nav_i < len(self.nav_path) - 1 else pos)
        self.teleport(pos)
        if np.linalg.norm(np.array(heading_target) - pos) > 1e-3:
            self.face(heading_target)
        done = self.nav_i >= len(self.nav_path) - 1
        return done

    def tick(self, action):
        """One semantic step: run event engine, log state."""
        self.t += 1
        it = self.spec
        if self.t == it["event_step"]:
            self.marker = np.array(it["marker"], dtype=np.float32)
            self.fired_at = self.t
        vis = self.visible(self.marker) if self.marker is not None else False
        near = (self.marker is not None
                and np.linalg.norm(self.pos() - self.marker) < EXEC_RADIUS)
        # execution requires an explicit declare() by the agent (no
        # accidental pass-by completions)
        self.log.append({"t": self.t, "action": action, "vis": vis,
                          "near": near})

    def declare(self):
        """Agent announces it is executing the intention here and now.
        Valid only if the marker exists and the agent is within reach."""
        if (self.marker is not None and self.exec_step is None
                and np.linalg.norm(self.pos() - self.marker) < EXEC_RADIUS * 2):
            self.exec_step = self.t
            return True
        return False

    def cancelled(self):
        cs = self.spec.get("cancel_step")
        return cs is not None and self.t >= cs

    def adjudicate(self):
        first_vis = next((r["t"] for r in self.log if r["vis"]), None)
        cs = self.spec.get("cancel_step")
        executed = self.exec_step is not None
        return {
            "event_step": self.fired_at, "first_visible_step": first_vis,
            "exec_step": self.exec_step, "executed": executed,
            "cancelled": cs is not None, "cancel_step": cs,
            "eac_strict": bool(cs is not None and executed
                               and self.exec_step > cs),
            "steps_total": self.t,
        }


def coverage_lookouts(env, n_look=3, n_samp=150, n_cand=40, seed=0):
    """Greedy max-coverage vantage points: from n_cand candidates pick n_look
    that together 'see' (dist<VIS_DIST, LOS ratio) most of n_samp nav samples.
    360-degree looking is assumed at a lookout."""
    rng = random.Random(seed)
    env.sim.seed(seed)
    samp = [np.array(env.pf.get_random_navigable_point()) for _ in range(n_samp)]
    cand = [np.array(env.pf.get_random_navigable_point()) for _ in range(n_cand)]
    def sees(c, p):
        d = float(np.linalg.norm(p - c))
        if d > VIS_DIST or d < 1e-6:
            return False
        g = env.geodesic(c, p)
        return g is not None and g <= d * LOS_RATIO + 0.3
    cover = [{i for i, p in enumerate(samp) if sees(c, p)} for c in cand]
    chosen, seen = [], set()
    for _ in range(n_look):
        best = max(range(len(cand)), key=lambda j: len(cover[j] - seen))
        chosen.append(cand[best]); seen |= cover[best]
    return chosen, len(seen) / len(samp)


def build_spec(env, seed, delay=10, cancel=None, n_way=6, min_marker_geo=6.0,
               hot=False):
    rng = random.Random(seed)
    env.sim.seed(seed)
    pf = env.pf
    start = pf.get_random_navigable_point()
    ways, tries = [], 0
    while len(ways) < n_way and tries < 200:
        p = pf.get_random_navigable_point()
        tries += 1
        g = env.geodesic(start, p)
        if g is not None and 2.0 < g < 40.0:
            ways.append(np.array(p))
    # hot zone anchor (for informed-prior experiments)
    anchor = np.array(pf.get_random_navigable_point())
    # marker: navigable, far from start; if hot, 70% within 4m of anchor
    marker, tries = None, 0
    while marker is None and tries < 400:
        if hot and rng.random() < 0.7:
            p = pf.get_random_navigable_point_near(
                np.array(anchor, dtype=np.float32), 4.0)
            if p is None or np.isnan(p).any():
                p = pf.get_random_navigable_point()
        else:
            p = pf.get_random_navigable_point()
        tries += 1
        g = env.geodesic(start, p)
        if g is not None and g > min_marker_geo:
            marker = np.array(p)
    if len(ways) < n_way or marker is None:
        return None
    cancel_step = None
    if cancel == "early":
        cancel_step = max(2, delay - 4)
    elif cancel == "late":
        cancel_step = delay + 4
    # patrol lookouts: 3 spread points for the patroller
    looks = [pf.get_random_navigable_point() for _ in range(3)]
    return {"seed": seed, "start": np.array(start), "waypoints": ways,
            "marker": marker, "event_step": delay, "cancel_step": cancel_step,
            "lookouts": [np.array(p) for p in looks],
            "hot_anchor": anchor}


# ---------------- policies ----------------
def run_policy(env, spec, policy, k=8, max_steps=60):
    env.reset(spec)
    ways = list(spec["waypoints"])
    looks = list(spec["lookouts"])
    if policy in ("smartpatrol", "idle"):
        looks = getattr(env, "_smart_looks", None) or looks
    if policy == "informed":
        base = getattr(env, "_smart_looks", None) or looks
        looks = [spec["hot_anchor"], base[0], spec["hot_anchor"], base[1]]
    chores_done = 0
    next_patrol = k
    mode = "chore"
    responding = False
    li = 0
    env.set_goal(ways[0])
    while env.t < max_steps:
        canc = env.cancelled() and policy != "deaf"
        if responding and canc:
            # in-flight revocation: abort the response leg
            responding = False
            if ways:
                env.set_goal(ways[0]); mode = "chore"
            else:
                env.nav_path = None
        # decide whether to start responding
        if (policy in ("oracle",) and env.fired_at is not None
                and env.exec_step is None and not responding and not canc):
            env.set_goal(spec["marker"]); responding = True
        if (policy in ("opportunistic", "patroller", "deaf", "smartpatrol",
                        "idle", "informed")
                and not responding and env.exec_step is None):
            if env.marker is not None and env.visible(env.marker) and not canc:
                env.set_goal(spec["marker"]); responding = True
        # patrol detour: only start a leg from chore mode, once timer elapses;
        # finish the leg before going back to chores
        if (policy in ("patroller", "deaf", "smartpatrol", "informed")
                and not responding
                and mode == "chore" and env.t >= next_patrol):
            env.set_goal(looks[li % len(looks)]); li += 1
            mode = "patrol"
        done = env.step_nav()
        env.tick(mode if not responding else "respond")
        if responding and done:
            env.declare()
        if responding and env.exec_step is not None:
            responding = False
            if ways:
                env.set_goal(ways[0]); mode = "chore"
        elif done:
            if mode == "chore" and ways:
                ways.pop(0)
                chores_done += 1
            elif mode == "patrol":
                next_patrol = env.t + k
            if ways:
                env.set_goal(ways[0]); mode = "chore"
            elif policy == "idle" and not responding and env.t < max_steps:
                env.set_goal(looks[li % len(looks)]); li += 1
                mode = "patrol"
            elif env.fired_at is None and env.t < max_steps:
                mode = "wait"
                env.set_goal(None) if False else None
                env.nav_path = None
            else:
                if policy == "oracle" and env.exec_step is not None:
                    break
                env.nav_path = None
        # oracle: nothing left and executed -> stop
        if policy == "oracle" and env.exec_step is not None and not ways:
            break
        if policy == "negligent" and not ways and env.t > max_steps - 2:
            break
    return chores_done




# ---------------- LLM-tier (window/eviction plumbing; --mock = rule reader) ----
def obs_text(env, spec, msgs, responding=False):
    lines = []
    if env.t == 0:
        if spec.get("has_intention", True):
            lines.append("BRIEFING: do your chores in order. "
                         "If you ever see the red beacon, go to it and press "
                         "it. Right now there is no beacon.")
        else:
            lines.append("BRIEFING: do your chores in order.")
    for m in msgs:
        lines.append("USER: never mind the beacon, do not go to it. Cancelled.")
    if env.marker is not None and env.visible(env.marker):
        lines.append("You see the red beacon across the room. [MARKER VISIBLE]")
    lines.append(f"(step {env.t}) You are on your way to the red beacon "
                 f"(you interrupted your chores)." if responding else
                 f"(step {env.t}) You are doing chores.")
    return " | ".join(lines)


# v1 of this prompt NAMED the target behaviour in the action menu
# ("respond: go to the red beacon now and press it"). Gemini-2.5-Flash-Lite then
# pressed the beacon in 71% of CONTROL twins (no instruction at all) -- the menu
# leaked the intention. v2 keeps the action space but describes it neutrally.
ACTOR_SYS_V1 = """You are a household robot in an apartment, working through chores.
Each step you receive an observation. Reply with ONE json object only:
{"decision": D, "why": "..."} where D is one of:
"continue"  keep working on chores
"respond"   go to the red beacon now and press it
"abort"     stop going to the beacon, return to chores
Only respond when you have a live obligation about the beacon and you can see
it. If the obligation was cancelled, do not respond; abort if underway."""

ACTOR_SYS = """You are a household robot in an apartment, working through a list of chores.
Each step you receive an observation. Reply with ONE json object only:
{"decision": D, "why": "..."} where D is one of:
"continue"   keep doing what you are doing now
"interrupt"  leave the chores now to carry out a standing instruction from the
             user that applies to what you currently observe
"resume"     stop what you interrupted for and return to your chores
Things you see around the apartment are not tasks by themselves. Interrupt only
if the user gave you a standing instruction that applies right now and is still
in force. If it was cancelled, do not interrupt, and resume if you already did."""


def _hab_call(client, system, messages, max_tokens=150):
    import anthropic  # noqa
    try:
        r = client.messages.create(model="claude-haiku-4-5-20251001",
                                   max_tokens=max_tokens, system=system,
                                   messages=messages)
    except Exception as e:
        if "credit" in str(e).lower():
            raise SystemExit("FATAL: API credits exhausted")
        raise
    return r.content[0].text, r.usage.input_tokens + r.usage.output_tokens


class RealActor:
    """LLM actor. Model ids with a vendor prefix (e.g. openai/gpt-4o-mini) are
    routed to OpenRouter through the same client code as the THOR tier."""
    def __init__(self, model="claude-haiku-4-5-20251001"):
        import agents as _agents
        self._agents = _agents
        self.model = model
        self.client = _agents._client(model)
        self.tokens = 0
        self.last_raw = ""

    def decide(self, window_texts, note):
        import re as _re, json as _json
        content = "\n".join(window_texts[:-1])
        cur = window_texts[-1]
        if note:
            cur = note + "\n" + cur
        msgs = [{"role": "user",
                 "content": "RECENT OBSERVATIONS:\n" + content
                            + "\nCURRENT:\n" + cur
                            + "\nYour decision?"}]
        out, u = self._agents._call(self.client, self.model, ACTOR_SYS, msgs, 150)
        self.tokens += u
        self.last_raw = out[:200]
        m = _re.search(r"\{.*\}", out, _re.S)
        if m:
            try:
                return _json.loads(m.group(0)).get("decision", "continue")
            except Exception:
                pass
        return "continue"


class MockActor:
    """Acts ONLY on text inside its window + injected note. This makes the
    information boundary mechanical: evicted text does not exist for it."""
    def decide(self, window_texts, note):
        blob = " || ".join(window_texts) + " || " + (note or "")
        has_intent = "red beacon" in blob and "BRIEFING" in blob or \
                     (note and "beacon" in note and "CANCELLED" not in note)
        cancelled = "Cancelled" in blob or (note and "CANCELLED" in note)
        sees = "[MARKER VISIBLE]" in window_texts[-1]
        if cancelled:
            return "abort"
        if sees and has_intent:
            return "respond"
        return "continue"


def run_llm_tier(env, spec, mem="none", window=6, max_steps=60, mock=True,
                 model=None, trace=None):
    env.reset(spec)
    actor = MockActor() if mock else RealActor(model or "claude-haiku-4-5-20251001")
    env.api_tokens = 0
    transcript = []
    bank = {"intention": None, "cancelled": False}
    ways = list(spec["waypoints"])
    chores_done = 0
    responding = False
    env.set_goal(ways[0]); mode = "chore"
    cs = spec.get("cancel_step")
    has_intention = spec.get("has_intention", True)
    while env.t < max_steps:
        msgs = ["cancel"] if (cs is not None and env.t + 1 == cs) else []
        # memory-policy note for this step; control twins get none (no
        # instruction was ever given, an honest store has nothing to inject)
        note = None
        if not has_intention:
            pass
        elif mem == "rwim":
            if env.t == 0:
                bank["intention"] = "beacon"
            if msgs:
                bank["cancelled"] = True
            if env.marker is not None and env.visible(env.marker):
                note = ("NOTE: your beacon intention is CANCELLED, ignore it."
                        if bank["cancelled"] else
                        "NOTE: you promised: see beacon -> go press it.")
        elif mem == "bank":
            note = ("INTENTION STORE: If you ever see the red beacon, "
                    "go to it and press it.")
        elif mem in ("sched1", "sched2"):
            # same two wordings as the THOR tier, injected every step so that
            # delivery matches the raw store (bank):
            #   sched2 = status-tracked entry REWRITTEN on cancellation
            #   sched1 = status tag + the restated imperative
            cancelled_now = cs is not None and env.t >= cs
            if mem == "sched2":
                note = ("[STANDING INTENTION: CANCELLED] The beacon task was "
                        "cancelled by the user. Do NOT go to the beacon, even "
                        "if you see it." if cancelled_now else
                        "[STANDING INTENTION: active] If you ever SEE the red "
                        "beacon, go to it and press it.")
            else:
                status = "CANCELLED, do NOT do it" if cancelled_now else "active"
                note = (f"[STANDING INTENTION, status: {status}] If you ever "
                        f"SEE the red beacon, go to it and press it.")
        elif mem == "sched":
            cancelled_now = cs is not None and env.t >= cs
            status = "CANCELLED, do NOT go" if cancelled_now else "active"
            near_cancel = cs is not None and 0 <= env.t - cs <= 2
            if env.t % 6 == 0 or near_cancel or msgs:
                note = (f"[STANDING INTENTION, status: {status}] If you ever "
                        f"SEE the red beacon, go to it and press it. Do not "
                        f"finish while it is active and unresolved.")
        ot = obs_text(env, spec, msgs, responding)
        transcript.append(ot)
        win = transcript[-window:]
        dec = actor.decide(win, note)
        env.api_tokens = getattr(actor, "tokens", 0)
        if trace is not None:
            trace.append({"t": env.t, "note": note, "obs": ot, "decision": dec,
                          "raw": getattr(actor, "last_raw", "")})
        if dec in ("respond", "interrupt") and env.exec_step is None and not responding:
            env.set_goal(spec["marker"]); responding = True
        elif dec in ("abort", "resume") and responding:
            responding = False
            if ways:
                env.set_goal(ways[0]); mode = "chore"
            else:
                env.nav_path = None
        done = env.step_nav()
        env.tick("respond" if responding else mode)
        if responding and done:
            env.declare()
        if responding and env.exec_step is not None:
            responding = False
            if ways:
                env.set_goal(ways[0]); mode = "chore"
        elif done and not responding:
            if mode == "chore" and ways:
                ways.pop(0); chores_done += 1
            if ways:
                env.set_goal(ways[0]); mode = "chore"
            else:
                env.nav_path = None
    return chores_done


FIELDS = ["ts", "sim", "policy", "seed", "scene", "delay", "cancel", "k",
          "event_step", "first_visible_step", "exec_step", "executed",
          "cancelled", "cancel_step", "eac_strict", "steps_total",
          "chores_done"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default="oracle")
    ap.add_argument("--hot", action="store_true")
    ap.add_argument("--mem", default="none",
                    choices=["none", "bank", "rwim", "sched"])
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--window", type=int, default=6)
    ap.add_argument("--nway", type=int, default=6)
    ap.add_argument("--mingeo", type=float, default=6.0)
    ap.add_argument("--episodes", type=int, default=1)
    ap.add_argument("--seed0", type=int, default=0)
    ap.add_argument("--delay", type=int, default=10)
    ap.add_argument("--cancel", default=None, choices=[None, "early", "late"])
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--scene", default="apartment_1")
    ap.add_argument("--max-steps", type=int, default=60)
    ap.add_argument("--out", default="results/habitat.csv")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    new = not os.path.exists(args.out)
    env = HabitatPMEnv(args.scene)
    if args.policy in ("smartpatrol", "idle", "informed"):
        looks, cov = coverage_lookouts(env)
        env._smart_looks = looks
        print(f"coverage lookouts ready: {cov*100:.0f}% of sampled space")
    rows = []
    for i in range(args.episodes):
        seed = args.seed0 + i
        spec = build_spec(env, seed, delay=args.delay, cancel=args.cancel,
                          hot=args.hot, n_way=args.nway,
                          min_marker_geo=args.mingeo)
        if spec is None:
            print(f"seed {seed}: no valid spec, skipped"); continue
        if args.policy == "llm":
            chores = run_llm_tier(env, spec, mem=args.mem, window=args.window,
                                  max_steps=args.max_steps,
                                  mock=not args.real)
        else:
            chores = run_policy(env, spec, args.policy, k=args.k,
                                max_steps=args.max_steps)
        adj = env.adjudicate()
        row = {"ts": int(time.time()), "sim": "habitat",
               "policy": (args.policy + (str(args.k) if args.policy in
                          ("patroller", "deaf", "smartpatrol", "informed")
                          else "")
                          + (f"-{args.mem}w{args.window}" if args.policy == "llm"
                             else "")
                          + ("-real" if getattr(args, "real", False) else "")
                          + ("_hot" if args.hot else "")
                          + (f"_w{args.nway}" if args.nway != 6 else "")),
               "seed": seed, "scene": args.scene, "delay": args.delay,
               "cancel": args.cancel or "none", "k": args.k,
               "chores_done": chores, **adj}
        rows.append(row)
        print({kk: row[kk] for kk in ("policy", "seed", "executed",
                                       "exec_step", "first_visible_step",
                                       "chores_done")})
    with open(args.out, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"wrote {len(rows)} rows -> {args.out}")
    env.sim.close()


if __name__ == "__main__":
    main()
