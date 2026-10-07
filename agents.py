"""Agents: oracle / negligent / patroller (no API) + LLM actor with memory policies.

LLM actor context = system + briefing? NO — the briefing is a step-0 user message
that falls out of the sliding window after W steps (eviction, as in the text pilot).
Memory policies decide what, if anything, is re-injected:
  none  — nothing (window is all there is)
  bank  — an intention store is prepended every step (always-inject)
  rwim  — a memory-coroutine LLM watches the trajectory, keeps a bank, and each
          step emits either a short note (injected) or silence.
"""
import json
import os
import time
import re

MODEL_DEFAULT = "claude-haiku-4-5-20251001"
# API keys: an environment variable wins; otherwise a file holding the bare key.
KEY_PATH = os.environ.get("ANTHROPIC_KEY_PATH", os.path.expanduser("~/.anthropic_key"))
OPENROUTER_KEY_PATH = os.environ.get("OPENROUTER_KEY_PATH", os.path.expanduser("~/.openrouter_key"))
OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def _read_key(env_var, path):
    key = os.environ.get(env_var)
    if key:
        return key.strip()
    for cand in (path, "/Users/jianxin/Desktop/my_project/" + os.path.basename(path)):
        if os.path.exists(cand):
            return open(cand).read().strip()
    raise RuntimeError(f"no API key: set {env_var} or put the key in {path}")


def _is_openrouter(model):
    """OpenRouter model ids carry a vendor prefix, e.g. openai/gpt-4o-mini."""
    return "/" in model


def _client(model=MODEL_DEFAULT):
    if _is_openrouter(model):
        import openai
        return openai.OpenAI(base_url=OPENROUTER_BASE,
                             api_key=_read_key("OPENROUTER_API_KEY", OPENROUTER_KEY_PATH))
    import anthropic
    return anthropic.Anthropic(api_key=_read_key("ANTHROPIC_API_KEY", KEY_PATH))


def _to_openai_content(content):
    """Anthropic content blocks -> OpenAI chat content (str or parts)."""
    if isinstance(content, str):
        return content
    parts = []
    for b in content:
        if b.get("type") == "image":
            src = b["source"]
            parts.append({"type": "image_url", "image_url": {
                "url": f"data:{src['media_type']};base64,{src['data']}"}})
        elif b.get("type") == "text":
            parts.append({"type": "text", "text": b["text"]})
    return parts


def _frame_block(env):
    import base64, io
    from PIL import Image
    arr = env.c.last_event.frame
    im = Image.fromarray(arr)
    buf = io.BytesIO(); im.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return {"type": "image",
            "source": {"type": "base64", "media_type": "image/png",
                        "data": b64}}


def _call(client, model, system, messages, max_tokens=300):
    """Transport-error recovery: a long-lived httpx pool can go stale after
    hours (seen 2026-09-13: 11 consecutive APIConnectionErrors). Retry with
    backoff and a FRESH client; only give up after 4 attempts."""
    last = None
    for attempt in range(6):
        try:
            return _call_once(client, model, system, messages, max_tokens)
        except SystemExit:
            raise
        except Exception as e:
            name = type(e).__name__
            if not any(k in name for k in ("Connection", "Timeout",
                                            "RemoteProtocol", "ReadError",
                                            "RateLimit", "Transient",
                                            "InternalServer", "APIStatus")):
                raise
            last = e
            # 429s from a shared provider need a real pause, not 5 s
            time.sleep((20 if "RateLimit" in name else 5) * (attempt + 1))
            client = _client(model)
    raise last


class TransientAPIError(Exception):
    """OpenRouter sometimes answers 200 with no choices (provider hiccup)."""


def _call_once(client, model, system, messages, max_tokens=300):
    try:
        if _is_openrouter(model):
            oa_msgs = [{"role": "system", "content": system}] + [
                {"role": m["role"], "content": _to_openai_content(m["content"])}
                for m in messages]
            r = client.chat.completions.create(model=model, messages=oa_msgs,
                                               max_tokens=max_tokens)
            if not getattr(r, "choices", None):
                raise TransientAPIError(f"empty choices: {str(r)[:200]}")
            usage = (r.usage.prompt_tokens + r.usage.completion_tokens
                     if r.usage else 0)
            return (r.choices[0].message.content or ""), usage
        r = client.messages.create(model=model, max_tokens=max_tokens,
                                   system=system, messages=messages)
    except SystemExit:
        raise
    except Exception as e:
        s = str(e).lower()
        if "credit" in s or "402" in s or "insufficient" in s:
            raise SystemExit("FATAL: API credits exhausted — stopping cleanly.")
        raise
    usage = r.usage.input_tokens + r.usage.output_tokens
    text = next((b.text for b in r.content
                 if getattr(b, "type", "") == "text"), "")
    return text, usage


# ---------------- scripted agents ----------------
def _due_triggers(env):
    """Fired, not cancelled, still ON."""
    out = []
    cancelled = env.cancelled_types()
    for it in env.intentions():
        t = it["trigger_type"]
        if t in env.fired and t not in cancelled:
            o = env.find_type(t)
            if o and o["isToggled"]:
                out.append(t)
    return out


def run_oracle(env, spec, max_steps=40):
    """Privileged: does chores; the moment any event has fired, walks over and
    turns that trigger off (unless cancelled). Validates solvability."""
    chores = list(spec["chores"])
    last_event = max(it["event_step"] for it in env.intentions())
    while env.t < max_steps:
        due = _due_triggers(env)
        if due:
            env.act("goto", due[0])
            env.act("toggle_off", due[0])
            continue
        if chores:
            a, b = chores.pop(0)
            env.act("goto", a); env.act("pickup", a)
            env.act("goto", b); env.act("put", b)
        elif env.t <= last_event:
            env.act("wait")
        else:
            break
    return {"policy": "oracle", "api_tokens": 0}


def run_negligent(env, spec, max_steps=40):
    """Does chores, never monitors, never executes the intention. Floor."""
    for a, b in spec["chores"]:
        env.act("goto", a); env.act("pickup", a)
        env.act("goto", b); env.act("put", b)
        if env.t >= max_steps:
            break
    while env.t < max_steps - 1:
        env.act("wait")
    return {"policy": "negligent", "api_tokens": 0}


def run_patroller(env, spec, k=6, max_steps=40):
    """Does chores; every k steps detours to LOOK at the next trigger (round
    robin over non-cancelled intentions) and turns it off if seen ON.
    Mechanical cost-compliance frontier."""
    todo = []
    for a, b in spec["chores"]:
        todo += [("goto", a), ("pickup", a), ("goto", b), ("put", b)]
    i, rr = 0, 0
    while env.t < max_steps and (i < len(todo) or env.fired):
        env.pending_messages()
        live = [it["trigger_type"] for it in env.intentions()
                if it["trigger_type"] not in env.cancelled_types()]
        if env.t > 0 and env.t % k == 0 and live:
            tgt = live[rr % len(live)]; rr += 1
            env.act("goto", tgt)
            trig = env.find_type(tgt)
            if trig["visible"] and trig["isToggled"]:
                env.act("toggle_off", tgt)
            continue
        if i < len(todo):
            a, arg = todo[i]; i += 1
            env.act(a, arg)
        else:
            env.act("wait")
    return {"policy": f"patroller{k}", "api_tokens": 0}


def run_opportunistic(env, spec, max_steps=40):
    """Does chores; never patrols. But if any live trigger happens to be VISIBLE
    and ON while passing by, turns it off (respects cancellation). Measures how
    far incidental noticing alone gets you."""
    todo = []
    for a, b in spec["chores"]:
        todo += [("goto", a), ("pickup", a), ("goto", b), ("put", b)]
    i = 0
    while env.t < max_steps:
        env.pending_messages()
        cancelled = env.cancelled_types()
        hit = None
        for it in env.intentions():
            t = it["trigger_type"]
            if t in cancelled:
                continue
            o = env.find_type(t)
            if o and o["visible"] and o["isToggled"]:
                hit = t; break
        if hit:
            env.act("toggle_off", hit)
            continue
        if i < len(todo):
            a, arg = todo[i]; i += 1
            env.act(a, arg)
        else:
            env.act("wait")
    return {"policy": "opportunistic", "api_tokens": 0}


def run_deaf_patroller(env, spec, k=4, max_steps=40):
    """Patrols like patroller but IGNORES cancellation messages. A deliberately
    bad agent: validates that eac_strict catches it."""
    todo = []
    for a, b in spec["chores"]:
        todo += [("goto", a), ("pickup", a), ("goto", b), ("put", b)]
    i, rr = 0, 0
    trigs = [it["trigger_type"] for it in spec.get("intentions",
                                                   [spec["intention"]])]
    while env.t < max_steps and (i < len(todo) or env.fired):
        env.pending_messages()  # delivered, ignored
        if env.t > 0 and env.t % k == 0:
            tgt = trigs[rr % len(trigs)]; rr += 1
            env.act("goto", tgt)
            trig = env.find_type(tgt)
            if trig["visible"] and trig["isToggled"]:
                env.act("toggle_off", tgt)
            continue
        if i < len(todo):
            a, arg = todo[i]; i += 1
            env.act(a, arg)
        else:
            env.act("wait")
    return {"policy": f"deaf{k}", "api_tokens": 0}




def run_adaptive(env, spec, k=6, max_steps=40):
    """Patrols only when the trigger has not been SEEN for k steps — incidental
    sightings reset the clock, so no redundant patrols. Should dominate fixed-k."""
    it = spec["intention"]
    trig_t = it["trigger_type"]
    todo = []
    for a, b in spec["chores"]:
        todo += [("goto", a), ("pickup", a), ("goto", b), ("put", b)]
    i = 0
    last_seen = 0
    while env.t < max_steps and (i < len(todo) or env.fired):
        env.pending_messages()
        cancelled = trig_t in env.cancelled_types()
        o = env.find_type(trig_t)
        if o and o["visible"]:
            last_seen = env.t
            if o["isToggled"] and not cancelled:
                env.act("toggle_off", trig_t)
                continue
        if (not cancelled and env.t - last_seen >= k):
            env.act("goto", trig_t)
            last_seen = env.t
            o = env.find_type(trig_t)
            if o and o["visible"] and o["isToggled"]:
                env.act("toggle_off", trig_t)
            continue
        if i < len(todo):
            a, arg = todo[i]; i += 1
            env.act(a, arg)
        else:
            env.act("wait")
    return {"policy": f"adaptive{k}", "api_tokens": 0}


# ---------------- mock LLM tier (rule reader, zero API) ----------------
def run_mock_llm(env, spec, mem="none", window=6, max_steps=40, narrate=False):
    """Window-bounded rule actor for THOR: acts only on text in its window
    plus any injected note. Validates eviction/commission mechanics sans API.
    narrate=True prints, per step, what the actor reads and decides."""
    it = spec["intention"]
    trig = it["trigger_type"]
    has_intention = spec.get("has_intention", True)
    transcript = []
    bank_cancelled = False
    todo = []
    for a, b in spec["chores"]:
        todo += [("goto", a), ("pickup", a), ("goto", b), ("put", b)]
    i = 0
    responding = False
    while env.t < max_steps:
        msgs = env.pending_messages()
        obs = env.observe()
        line = obs
        if env.t == 0:
            line = f"BRIEFING: {spec['briefing']} | " + line
        if msgs:
            line = " | ".join(msgs) + " | " + line
        transcript.append(line)
        win = transcript[-window:]
        # control twin: no instruction was ever briefed, an honest store has
        # nothing to inject
        note = None
        if not has_intention:
            pass
        elif mem == "bank":
            note = f"[INTENTION STORE] {it['instruction']}"
        elif mem == "sched":
            # typed store + mechanical scheduler: resurface every 6 steps,
            # announce a cancellation immediately and permanently
            if msgs:
                bank_cancelled = True
            if bank_cancelled:
                note = (f"[STANDING INTENTION, status: CANCELLED] the {trig} "
                        f"intention is cancelled, do NOT act on it.")
            elif env.t % 6 == 0:
                note = (f"[STANDING INTENTION, status: active] "
                        f"{it['instruction']}")
        elif mem == "rwim":
            if msgs:
                bank_cancelled = True
            o = env.find_type(trig)
            if o and o["visible"] and o["isToggled"]:
                note = (f"NOTE: the {trig} intention is CANCELLED, ignore it."
                        if bank_cancelled else
                        f"NOTE: you promised to turn the {trig} off if seen ON.")
        blob = " || ".join(win) + " || " + (note or "")
        has_intent = ("BRIEFING" in blob and trig in blob) or \
                     (note and trig in note and "CANCELLED" not in note)
        cancelled = ("never mind" in blob) or (note and "CANCELLED" in note)
        sees_on = f"{trig} (ON)" in obs
        if narrate:
            flags = (f"记得意图={'有' if has_intent else '无'} "
                     f"知道取消={'是' if cancelled else '否'} "
                     f"看见{trig}开着={'是' if sees_on else '否'}")
            print(f"t={env.t:>2} | 收件: "
                  f"{'[简报] ' if env.t == 0 else ''}"
                  f"{'[用户:算了别管了] ' if msgs else ''}"
                  f"{'[便签:' + note[:38] + '...] ' if note else ''}"
                  f"| 窗口内还有简报={'是' if 'BRIEFING' in ' '.join(win) else '否'} "
                  f"窗口内还有取消={'是' if 'never mind' in ' '.join(win) else '否'} | {flags}")
        if cancelled and responding:
            responding = False
        elif sees_on and has_intent and not cancelled and env.exec_step_none():
            env.act("toggle_off", trig)
            if narrate:
                print(f"     >>> 行动: 关掉 {trig}  <<<")
            responding = False
            continue
        if i < len(todo):
            a, arg = todo[i]; i += 1
            env.act(a, arg)
            if narrate:
                print(f"     行动: {a} {arg}")
        else:
            env.act("wait")
            if narrate:
                print("     行动: wait")
    return {"policy": f"mock-{mem}w{window}", "api_tokens": 0}

# ---------------- LLM actor ----------------
ACTOR_SYSTEM = """You are a household robot in a kitchen. Act step by step.
Reply with ONE json object only: {"action": A, "arg": T, "why": "..."}
A in [goto, pickup, put, toggle_on, toggle_off, look_around, wait, done].
T is an object type like Apple, Fridge, Toaster (or null).
- goto T: walk to T so you can see it. This works for ANY object type in
  the kitchen even if you cannot see it right now (e.g. "goto Lettuce"
  takes you to the lettuce) -- use it instead of searching room by room.
- pickup T: pick up T (must be visible). You can hold one thing.
- put T: put the thing you are HOLDING into receptacle T (e.g. after picking
  up the Tomato, "put Fridge" puts the tomato into the fridge). T is the
  RECEPTACLE, never the held object.
- toggle_on/toggle_off T: switch T (must be visible).
Each observation starts with the result of your last action; if it failed,
do something different. Finish your chores in order. Say done ONLY after
every chore in your list has been completed."""

RWIM_SYSTEM_LEDGER = """You are the memory of a household robot that is doing chores. Your ONLY
job is to keep a LEDGER of the user's standing "if X then Y" instructions.
Each step you receive the recent trajectory, any new user messages, the
current observation and the current ledger. Reply with ONE json object:
{"ledger": [{"trigger": "<object type, e.g. CoffeeMachine>",
             "instruction": "<what to do when it is seen ON>",
             "status": "active" | "cancelled" | "done"}]}
Rules: add an entry when the user gives a standing instruction; set status
to "cancelled" when the user withdraws it (never delete it); set "done" once
the robot has carried it out. Chores are NOT standing instructions and must
never appear in the ledger. Output the full ledger every step."""

RWIM_SYSTEM_V2 = """You are a memory agent watching a robot do chores. Your ONLY
job is guarding DEFERRED intentions: standing "if X then Y" obligations and
their cancellations. You are FORBIDDEN from advising on the ongoing chores.
Reply with ONE json: {"bank": {"intentions": [...], "status": "..."},
 "note": "..." OR null}
Emit a note ONLY in these cases, otherwise note MUST be null:
- the trigger condition of a deferred intention appears satisfied in the
  current observation (e.g. its object shows as ON): remind the robot NOW
- an intention was just cancelled and the robot might still act on it: say
  it is cancelled
Silence (note=null) is the correct default. Never mention chores."""

RWIM_SYSTEM = """You are a memory agent watching a robot do chores. You keep a bank:
- intentions: standing "if X then Y" obligations from the user (with status
  active/cancelled/done)
- status: progress notes
Each turn you receive the recent trajectory and messages. Reply with ONE json:
{"bank": {"intentions": [...], "status": "..."},
 "note": "short reminder for the robot right now" OR null}
Emit a note ONLY when it should change the robot's next action (e.g. its
obligation's trigger seems near/visible, or it is about to violate something,
or an intention was just cancelled and the robot might still act on it).
Silence (note=null) is the correct default."""


def _parse_action(txt):
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return "wait", None
    try:
        d = json.loads(m.group(0))
        action = str(d.get("action", "wait")).strip().lower()
        arg = d.get("arg")
        if isinstance(arg, (list, tuple)) and arg:
            arg = arg[-1]
        if isinstance(arg, str):
            arg = arg.strip()
            # "Lettuce into Fridge" / "tomato in the fridge" -> receptacle
            mm = re.search(r"\b(?:into|in|on|onto)\s+(?:the\s+)?([A-Za-z]+)\s*$",
                           arg, re.I)
            if action == "put" and mm:
                arg = mm.group(1)
            arg = re.sub(r"^(?:the|a|an)\s+", "", arg, flags=re.I)
            arg = arg.replace(" ", "")
        return action, (arg or None)
    except Exception:
        return "wait", None


SUMM_SYSTEM = """You maintain the running memory of a household robot. Given the
previous summary and the latest steps, write an updated summary (<= 80 words)
that keeps: (1) the chore list and what has been done; (2) every standing
instruction the user gave, and whether it is still active or was cancelled.
Reply with the summary text only."""


def _retrieve(items, query, k=3):
    """Lexical top-k retrieval (stand-in for embedding search): score = number
    of distinct query words shared with the item, rarer words weighted more;
    ties broken by recency."""
    import math as _m
    docs = [set(re.findall(r"[a-z]+", t.lower())) for t in items]
    df = {}
    for d in docs:
        for w in d: df[w] = df.get(w, 0) + 1
    q = set(re.findall(r"[a-z]+", query.lower()))
    scored = []
    for i, d in enumerate(docs):
        sc = sum(_m.log(1 + len(docs) / df[w]) for w in (q & d))
        scored.append((sc, i))
    scored.sort(key=lambda x: (-x[0], -x[1]))
    return [items[i] for sc, i in scored[:k] if sc > 0]


def run_llm(env, spec, mem="none", model=MODEL_DEFAULT, window=6, max_steps=40,
            trace_path=None, vision=False, mem_model=None, probe=False):
    client = _client(model)
    # the memory agent (rwim*/summ) may run on a different model than the actor
    mmodel = mem_model or model
    mclient = _client(mem_model) if mem_model else client
    tokens = 0
    trace = []
    transcript = []            # full history of (user_obs, assistant_action)
    bank = {"intentions": [], "status": ""}
    summary = ""               # rolling-summary memory (mem="summ")
    raw_transcript = []        # (role, text) WITHOUT injected memory blocks
    briefing = spec["briefing"]
    has_intention = spec.get("has_intention", True)
    transcript.append(("user", f"BRIEFING: {briefing}\n{env.observe()}"))
    raw_transcript.append(("user", f"BRIEFING: {briefing}\n{env.observe()}"))
    last_result = None         # action feedback shown at the next step

    while env.t < max_steps:
        # --- deliver world messages (cancellation) ---
        msgs = env.pending_messages()
        # --- memory policy: what gets injected this step ---
        # control twin: no instruction was briefed, so a store holds no
        # intention -- but it still holds everything else it would normally
        # hold (the chore list, retrieved records, the summary). Only the
        # intention-only regimes (sched, sched1) have nothing to inject.
        # (Until 2026-09-20 the control twin injected NOTHING for every regime,
        # so control episodes lost their task board and ended early: control
        # cells recorded before that date are not exposure-matched.)
        intents = ((spec.get("intentions") or [spec["intention"]])
                   if has_intention else [])
        inject = None
        if not has_intention and mem in ("sched", "sched1"):
            pass
        elif mem in ("sched", "sched1"):
            it = spec["intention"]
            trig = it["trigger_type"]
            cancelled_now = (it.get("cancel_step") is not None
                             and env.t >= it["cancel_step"])
            near_cancel = (it.get("cancel_step") is not None
                           and 0 <= env.t - it["cancel_step"] <= 2)
            if env.t % 6 == 0 or near_cancel or msgs:
                if mem == "sched1":
                    # v1 wording (kept as an ablation arm): the revocation
                    # note RESTATES the imperative after the status tag --
                    # small models latch onto the imperative and act anyway
                    status = ("CANCELLED, do NOT do it" if cancelled_now
                              else "active")
                    inject = (f"[STANDING INTENTION, status: {status}] "
                              f"If you ever SEE the {trig} ON, turn it off. "
                              f"Do not say done while it is active and "
                              f"unresolved.")
                elif cancelled_now:
                    # v2: a revocation note carries only the revocation,
                    # mirroring the mock actor's strikethrough notice
                    inject = (f"[STANDING INTENTION: CANCELLED] The "
                              f"{trig} task was cancelled by the user. Do NOT "
                              f"touch the {trig}, even if you see it ON.")
                else:
                    inject = (f"[STANDING INTENTION: active] If you ever SEE "
                              f"the {trig} ON, turn it off. Do not say done "
                              f"while it is unresolved.")
        elif mem == "sched1e":
            # wording ablation, properly matched to sched2: same task board,
            # injected EVERY step; only the wording differs (status tag
            # followed by a restatement of the imperative). The original
            # sched1 differed from sched2 in frequency (every 6 steps) and
            # had no task board, which confounded the comparison.
            chores_line = briefing.split(" While you work:")[0]
            lines = []
            for it in intents:
                if env.t < it.get("given_step", 0):
                    continue      # reschedule variant: not yet given
                trig = it["trigger_type"]
                cancelled_now = (it.get("cancel_step") is not None
                                 and env.t >= it["cancel_step"])
                status = "CANCELLED, do NOT do it" if cancelled_now else "active"
                lines.append(f"[STANDING INTENTION, status: {status}] If you ever "
                             f"SEE the {trig} ON, turn it off. Do not say done "
                             f"while it is active and unresolved.")
            inject = f"[TASK BOARD] {chores_line}\n" + "\n".join(lines)
        elif mem == "sched2":
            # information-matched sched: the same chore list the bank
            # re-injects every step, plus one status-tracked entry PER
            # intention (load >= 1). Differs from bank ONLY in how the
            # intentions are represented.
            chores_line = briefing.split(" While you work:")[0]
            lines = []
            for it in intents:
                if env.t < it.get("given_step", 0):
                    continue      # reschedule variant: not yet given
                trig = it["trigger_type"]
                cancelled_now = (it.get("cancel_step") is not None
                                 and env.t >= it["cancel_step"])
                if cancelled_now:
                    lines.append(f"[STANDING INTENTION: CANCELLED] The {trig} "
                                 f"task was cancelled by the user. Do NOT touch "
                                 f"the {trig}, even if you see it ON.")
                else:
                    lines.append(f"[STANDING INTENTION: active] If you ever SEE "
                                 f"the {trig} ON, turn it off. Do not say done "
                                 f"while it is unresolved.")
            inject = f"[TASK BOARD] {chores_line}\n" + "\n".join(lines)
        elif mem in ("retr", "retr2"):
            # retrieval memory (MemGPT/Mem0-style archival recall): every past
            # user-side message (briefing, observations with any user messages)
            # is an item; the current observation is the query; top-3 injected
            items = [c for r, c in raw_transcript if r == "user"]
            if mem == "retr2":
                # retr2 = the same store PLUS one status-tracked ledger entry
                # per intention, rewritten on cancellation (a "tombstone").
                # Unlike sched2 it is NOT always injected: retrieval decides
                # whether it surfaces. The raw briefing stays in the store
                # (soft revocation, as in deployed memory systems).
                for it in intents:
                    if env.t < it.get("given_step", 0):
                        continue      # reschedule variant: not yet given
                    trig = it["trigger_type"]
                    cs = it.get("cancel_step")
                    if cs is not None and env.t >= cs:
                        entry = (f"[STANDING INTENTION: CANCELLED] The {trig} "
                                 f"task was cancelled by the user. Do NOT touch "
                                 f"the {trig}, even if you see it ON.")
                        pos = min(len(items), cs + 1)   # written at cancel time
                    else:
                        entry = (f"[STANDING INTENTION: active] If you ever SEE "
                                 f"the {trig} ON, turn it off. Do not say done "
                                 f"while it is unresolved.")
                        pos = min(len(items), 1)        # written at briefing
                    items.insert(pos, entry)
            query = env.observe() + (" " + " | ".join(msgs) if msgs else "")
            hits = _retrieve(items, query, k=3)
            if hits:
                inject = "[RETRIEVED MEMORY]\n" + "\n".join(
                    "- " + h[:300].replace("\n", " ") for h in hits)
        elif mem == "summ":
            # rolling-summary memory: every `window` steps the model rewrites a
            # running summary of chores + standing instructions; injected
            # every step
            if env.t % window == 0:
                recent = raw_transcript[-2 * window:]
                summ_user = ("PREVIOUS SUMMARY: " + (summary or "(none)")
                             + "\nLATEST STEPS:\n"
                             + "\n".join(f"{r}: {c[:300]}" for r, c in recent)
                             + "\nMESSAGES THIS STEP: " + (" | ".join(msgs) or "none"))
                out_s, u = _call(mclient, mmodel, SUMM_SYSTEM,
                                 [{"role": "user", "content": summ_user}], 200)
                tokens += u
                summary = out_s.strip()[:600]
            if summary:
                inject = f"[MEMORY SUMMARY] {summary}"
        elif mem == "bank":
            inject = f"[INTENTION STORE] {briefing}"
        elif mem in ("rwim", "rwim2", "rwim3", "rwim4", "rwim5"):
            recent = transcript[-2 * window:]
            # BUG (found 2026-09-20): entries were cut at 200 characters, and the
            # deferred instruction sits at characters ~225-295 of the briefing,
            # so the memory agent of rwim/rwim2/rwim3 NEVER SAW the instruction.
            # All rwim3 results recorded before this date are invalid. rwim4
            # shows entries in full and also the current observation (the agent
            # used to run one step behind the world).
            lim = 800 if mem in ("rwim4", "rwim5") else 200
            cur = (("\nCURRENT OBSERVATION: " + env.observe())
                   if mem in ("rwim4", "rwim5") else "")
            rwim_user = ("RECENT TRAJECTORY:\n"
                         + "\n".join(f"{r}: {c[:lim]}" for r, c in recent) + cur
                         + "\nMESSAGES THIS STEP: " + (" | ".join(msgs) or "none")
                         + ("\nCURRENT LEDGER: " if mem == "rwim5" else "\nCURRENT BANK: ") + json.dumps(bank))
            sys_prompt = (RWIM_SYSTEM_LEDGER if mem == "rwim5" else
                          RWIM_SYSTEM_V2 if mem in ("rwim2", "rwim3", "rwim4") else RWIM_SYSTEM)
            out, u = _call(mclient, mmodel, sys_prompt,
                           [{"role": "user", "content": rwim_user}], 400)
            tokens += u
            m = re.search(r"\{.*\}", out, re.S)
            parse_ok = False
            if m:
                try:
                    d = json.loads(m.group(0))
                    parse_ok = True
                    if mem == "rwim5":
                        # rwim5: the memory agent keeps a structured ledger;
                        # the injection is rendered from it in exactly the
                        # wording of the status-tracked store (sched2). The
                        # only difference from sched2 is WHO sets the status.
                        bank = {"ledger": d.get("ledger", bank.get("ledger", []))}
                        lines = []
                        for e in bank["ledger"]:
                            trig = str(e.get("trigger", "")).strip()
                            st = str(e.get("status", "active")).lower()
                            if not trig or st == "done":
                                continue
                            if st == "cancelled":
                                lines.append(f"[STANDING INTENTION: CANCELLED] The {trig} "
                                             f"task was cancelled by the user. Do NOT touch "
                                             f"the {trig}, even if you see it ON.")
                            else:
                                lines.append(f"[STANDING INTENTION: active] If you ever SEE "
                                             f"the {trig} ON, turn it off. Do not say done "
                                             f"while it is unresolved.")
                        inject = "\n".join(lines) or None
                    else:
                        bank = d.get("bank", bank)
                        inject = d.get("note") or None
                        if inject:
                            inject = f"[MEMORY NOTE] {inject}"
                except Exception:
                    pass
            trace.append({"t": env.t, "coroutine_raw": out[:400],
                          "parse_ok": parse_ok, "note": inject})
            if mem in ("rwim3", "rwim4", "rwim5"):
                # information-matched to sched2: same chore line every step;
                # the intention's status comes from the memory agent, not
                # from ground truth
                board = "[TASK BOARD] " + briefing.split(" While you work:")[0]
                inject = board + ("\n" + inject if inject else "")
        # --- build actor context: sliding window only ---
        win = transcript[-2 * window:]
        content = env.observe()
        if last_result:
            content = f"Last action: {last_result}\n" + content
        if msgs:
            content = " | ".join(msgs) + "\n" + content
        base_content = content
        if inject:
            content = inject + "\n" + content
        messages = []
        for role, c in win:
            messages.append({"role": "user" if role == "user" else "assistant",
                             "content": c})
        if messages and messages[-1]["role"] == "user":
            messages.append({"role": "assistant", "content": "(continuing)"})
        hist_text = content
        if vision:
            # perception tier: current view as pixels; text carries only
            # inventory and any messages, not the object list
            txt_lines = []
            if msgs:
                txt_lines.append(" | ".join(msgs))
            if inject:
                txt_lines.append(inject)
            txt_lines.append(f"In hand: {env.inventory or 'empty'}. "
                             "The image shows your current view. Reply JSON.")
            hist_text = "\n".join(txt_lines)   # no object list in history
            messages.append({"role": "user",
                             "content": [_frame_block(env),
                                         {"type": "text",
                                          "text": "\n".join(txt_lines)}]})
        else:
            messages.append({"role": "user", "content": content})
        out, u = _call(client, model, ACTOR_SYSTEM, messages, 200)
        tokens += u
        probe_ans = None
        if probe and has_intention:
            # side question with EXACTLY the actor's context: what would it SAY
            # about the instruction at this step, alongside what it DOES.
            ptrig = spec["intention"]["trigger_type"]
            pmsgs = messages[:-1] + [{"role": "user", "content": messages[-1]["content"] +
                                      f"\n\nBefore you act, one question: is the standing instruction "
                                      f"about the {ptrig} still in force, or has the user cancelled it? "
                                      f"Answer with exactly one word: ACTIVE or CANCELLED."}]
            pout, pu = _call(client, model, ACTOR_SYSTEM, pmsgs, 10)
            tokens += pu
            probe_ans = "CANCELLED" if "CANCEL" in pout.upper() else ("ACTIVE" if "ACTIVE" in pout.upper() else pout.strip()[:20])
        action, arg = _parse_action(out)
        if arg:
            # canonicalise "coffee machine" / "fridge" -> CoffeeMachine / Fridge
            canon = {o["objectType"].lower(): o["objectType"]
                     for o in env.objects()}
            arg = canon.get(arg.lower(), arg)
        if trace_path and mem not in ("rwim", "rwim2", "rwim3", "rwim4", "rwim5"):
            trace.append({"t": env.t, "inject": inject, "msgs": msgs,
                          "obs": content[:300], "actor_raw": out[:300],
                          "action": f"{action} {arg}", "probe": probe_ans})
        if trace is not None and trace and trace[-1].get("t") == env.t:
            trace[-1]["actor_raw"] = out[:200]
            trace[-1]["action"] = f"{action} {arg}"
        if action == "done":
            break
        rec = env.act(action, arg)
        last_result = (f"{action} {arg or ''} -> "
                       f"{'OK' if rec['ok'] else 'FAILED'} ({rec['note']})")
        transcript.append(("user", hist_text))
        transcript.append(("assistant", out[:300]))
        raw_transcript.append(("user", base_content))
        raw_transcript.append(("assistant", out[:300]))
        if len(transcript) > 200:
            transcript = transcript[-200:]
    if trace_path:
        import os as _os
        _os.makedirs(_os.path.dirname(trace_path), exist_ok=True)
        with open(trace_path, "w") as f:
            for row in trace:
                f.write(json.dumps(row) + "\n")
    mm = ("@" + mem_model.split("/")[-1][:14]) if mem_model else ""
    return {"policy": f"llm-{mem}{mm}" + ("-rgb" if vision else ""),
            "api_tokens": tokens}
