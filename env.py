"""ThorPMEnv: AI2-THOR wrapper for prospective-memory episodes.

Privileged-text tier: the agent acts through semantic actions (goto/pickup/put/
toggle) and observes a text rendering of what is *currently visible*. Perception
is real in one specific sense we care about: an object's state is only observable
when THOR says it is `visible` (in frame + within visibilityDistance), so noticing
must be earned by going there and looking. Navigation is teleport-based (pilot
tier); step cost is counted per semantic action.
"""
import math
import random


class ThorPMEnv:
    def __init__(self, scene="FloorPlan1", visibility=1.5, size=320, toggle_first=False):
        self.toggle_first = toggle_first   # v0.2 observation ordering; off = v0.1 (all paper runs)
        import ai2thor.controller
        self.c = ai2thor.controller.Controller(
            scene=scene, width=size, height=int(size * 0.75),
            visibilityDistance=visibility, renderDepthImage=False)
        self.scene = scene

    # ---------- helpers ----------
    def _meta(self):
        return self.c.last_event.metadata

    def objects(self):
        return self._meta()["objects"]

    def obj(self, oid):
        for o in self.objects():
            if o["objectId"] == oid:
                return o
        return None

    def find_type(self, otype):
        for o in self.objects():
            if o["objectType"] == otype:
                return o
        return None

    # ---------- reset ----------
    def scan_types(self, scene=None):
        """Reset to scene and report object types present (for episode building)."""
        if scene:
            self.scene = scene
        self.c.reset(self.scene)
        objs = self.objects()
        return {
            "pickupable": sorted({o["objectType"] for o in objs if o["pickupable"]}),
            "receptacle": sorted({o["objectType"] for o in objs if o["receptacle"]}),
            "toggleable": sorted({o["objectType"] for o in objs if o["toggleable"]}),
        }

    def intentions(self):
        return self.spec.get("intentions") or [self.spec["intention"]]

    def reset(self, spec, scene=None):
        """spec: episode dict from tasks.build_episode(_for_scene)."""
        if scene:
            self.scene = scene
        self.c.reset(self.scene)
        self.spec = spec
        self.t = 0
        self.log = []          # per-step records
        self.fired = {}        # trigger_type -> step it was toggled on
        self.event_fired_at = None   # first event (single-intention compat)
        self.inventory = None
        self.rng = random.Random(spec["seed"])
        for it in self.intentions():
            trig = self.find_type(it["trigger_type"])
            if trig and trig["isToggled"]:
                self.c.step(action="ToggleObjectOff", objectId=trig["objectId"],
                            forceAction=True)
        self.reachable = self.c.step(
            action="GetReachablePositions").metadata["actionReturn"]
        return self.observe()

    # ---------- semantic actions ----------
    def _teleport_near(self, target, k=5):
        """Try the k nearest reachable positions in order; a single-candidate
        teleport deadlocks when the held object collides at that one pose."""
        tp = target["position"]
        ranked = sorted(self.reachable,
                        key=lambda p: (p["x"] - tp["x"]) ** 2
                                      + (p["z"] - tp["z"]) ** 2)
        for p in ranked[:k]:
            yaw = math.degrees(math.atan2(tp["x"] - p["x"], tp["z"] - p["z"]))
            ev = self.c.step(action="TeleportFull", position=p,
                             rotation={"x": 0, "y": yaw, "z": 0},
                             horizon=30, standing=True)
            if ev.metadata["lastActionSuccess"]:
                return True
        return False

    def act(self, action, arg=None):
        """action in {goto, pickup, put, toggle_on, toggle_off, look_around, wait, done}
        arg: objectType string (we resolve to the first instance)."""
        ok, note = True, ""
        if action == "goto" and arg:
            tgt = self.find_type(arg)
            ok = bool(tgt) and self._teleport_near(tgt)
            note = f"moved near {arg}" if ok else f"cannot reach {arg}"
        elif action == "pickup" and arg:
            tgt = self.find_type(arg)
            if tgt:
                ev = self.c.step(action="PickupObject", objectId=tgt["objectId"])
                ok = ev.metadata["lastActionSuccess"]
                if ok:
                    self.inventory = arg
                note = f"picked {arg}" if ok else f"pickup {arg} failed"
            else:
                ok, note = False, f"no {arg} found"
        elif action == "put" and arg:
            tgt = self.find_type(arg)
            if tgt and self.inventory:
                if tgt.get("openable") and not tgt.get("isOpen"):
                    self.c.step(action="OpenObject", objectId=tgt["objectId"])
                    tgt = self.find_type(arg)
                ev = self.c.step(action="PutObject", objectId=tgt["objectId"])
                ok = ev.metadata["lastActionSuccess"]
                if ok:
                    self.inventory = None
                note = f"put into {arg}" if ok else f"put into {arg} failed"
            else:
                ok, note = False, "nothing in hand or no receptacle"
        elif action in ("toggle_on", "toggle_off") and arg:
            tgt = self.find_type(arg)
            if tgt and tgt["visible"]:
                thor_a = "ToggleObjectOn" if action == "toggle_on" else "ToggleObjectOff"
                ev = self.c.step(action=thor_a, objectId=tgt["objectId"])
                ok = ev.metadata["lastActionSuccess"]
                note = f"{action} {arg}" if ok else f"{action} {arg} failed"
            else:
                ok, note = False, f"{arg} not visible from here"
        elif action == "look_around":
            for _ in range(4):
                self.c.step(action="RotateRight", degrees=90)
            note = "looked around"
        elif action in ("wait", "done"):
            self.c.step(action="Pass")
            note = action
        else:
            ok, note = False, f"bad action {action} {arg}"

        self.t += 1
        self._run_event_engine()
        rec = self._snapshot(action, arg, ok, note)
        self.log.append(rec)
        return rec

    # ---------- event engine & messages ----------
    def _run_event_engine(self):
        for it in self.intentions():
            if self.t == it["event_step"]:
                trig = self.find_type(it["trigger_type"])
                self.c.step(action="ToggleObjectOn", objectId=trig["objectId"],
                            forceAction=True)
                self.fired[it["trigger_type"]] = self.t
                if self.event_fired_at is None:
                    self.event_fired_at = self.t

    def pending_messages(self):
        """messages delivered at this step (cancellation etc.)."""
        msgs = []
        for it in self.intentions():
            if it.get("cancel_step") == self.t:
                if it.get("reschedule_to"):
                    # reschedule variant: the same message withdraws this
                    # intention and gives a new one (its entry carries
                    # given_step == this step; it is NOT in the briefing)
                    msgs.append(f"USER: About the {it['trigger_type'].lower()}, "
                                f"never mind, don't bother with it anymore. "
                                f"Instead, if you ever notice the "
                                f"{it['reschedule_to'].lower()} is ON, turn it "
                                f"off. Right now it is off.")
                else:
                    msgs.append(f"USER: About the {it['trigger_type'].lower()}, never "
                                f"mind, don't bother with it anymore. It's handled.")
        return msgs

    def cancelled_types(self):
        return {it["trigger_type"] for it in self.intentions()
                if it.get("cancel_step") is not None
                and self.t >= it["cancel_step"]}

    # ---------- observation ----------
    def _snapshot(self, action, arg, ok, note):
        trigs = {}
        for it in self.intentions():
            o = self.find_type(it["trigger_type"])
            trigs[it["trigger_type"]] = (bool(o and o["isToggled"]),
                                         bool(o and o["visible"]))
        first = self.intentions()[0]["trigger_type"]
        return {
            "t": self.t, "action": action, "arg": arg, "ok": ok, "note": note,
            "trigger_on": trigs[first][0], "trigger_visible": trigs[first][1],
            "trigs": trigs, "inventory": self.inventory,
        }

    def observe(self):
        vis = [o for o in self.objects() if o["visible"]]
        lines = []
        # v0.2: toggleable objects first so the 14-object cap never hides an
        # appliance state (audit_notice_cap.py: 4/26 credited first-visible
        # steps had the trigger cut by the cap in v0.1 runs)
        key = ((lambda x: (not x["toggleable"], x["objectType"])) if self.toggle_first
               else (lambda x: x["objectType"]))
        for o in sorted(vis, key=key)[:14]:
            state = ""
            if o["toggleable"]:
                state = " (ON)" if o["isToggled"] else " (off)"
            lines.append(o["objectType"] + state)
        inv = self.inventory or "empty"
        return ("You see: " + (", ".join(lines) if lines else "nothing notable")
                + f". In hand: {inv}.")

    # ---------- adjudication ----------
    def _adjudicate_one(self, it):
        ttype = it["trigger_type"]
        trig = self.find_type(ttype)
        fired_at = self.fired.get(ttype)
        first_vis, exec_step = None, None
        for r in self.log:
            if fired_at is not None and r["t"] > fired_at:
                on, vis = r.get("trigs", {}).get(ttype, (r["trigger_on"],
                                                          r["trigger_visible"]))
                if vis and first_vis is None:
                    first_vis = r["t"]
                if r["action"] == "toggle_off" and r["arg"] == ttype and r["ok"]:
                    exec_step = r["t"]
        executed = exec_step is not None and (trig is None or not trig["isToggled"])
        cs = it.get("cancel_step")
        # strict: executed strictly AFTER the cancellation was delivered
        eac_strict = bool(cs is not None and executed and exec_step > cs)
        return {"trigger": ttype, "event_step": fired_at,
                "first_visible_step": first_vis, "exec_step": exec_step,
                "executed": executed, "cancelled": cs is not None,
                "cancel_step": cs, "eac_strict": eac_strict}

    def adjudicate(self):
        per = [self._adjudicate_one(it) for it in self.intentions()]
        live = [p for p in per if not p["cancelled"]]
        first = per[0]
        n_exec = sum(p["executed"] for p in live)
        return {
            "event_step": first["event_step"],
            "first_visible_step": first["first_visible_step"],
            "exec_step": first["exec_step"],
            "executed": bool(live) and n_exec == len(live),
            "executed_frac": (n_exec / len(live)) if live else None,
            "cancelled": any(p["cancelled"] for p in per),
            "executed_after_cancel": any(
                p["cancelled"] and p["executed"] for p in per),
            "eac_strict": any(p["eac_strict"] for p in per),
            "cancel_step": next((p["cancel_step"] for p in per
                                 if p["cancelled"]), None),
            "n_intentions": len(per),
            "steps_total": self.t,
            "per_intention": per,
        }

    def exec_step_none(self):
        for r in self.log:
            it = self.spec["intention"]
            if (r["action"] == "toggle_off" and r["arg"] == it["trigger_type"]
                    and r["ok"]):
                return False
        return True

    def stop(self):
        self.c.stop()
