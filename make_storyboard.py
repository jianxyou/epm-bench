#!/usr/bin/env python3
"""Render one episode as an annotated storyboard (contact sheet).
Usage: python3 make_storyboard.py [--mem bank|sched] [--seed 1]
Output: results/storyboard_<mem>_s<seed>.png
"""
import argparse, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agents
from env import ThorPMEnv
from PIL import Image, ImageDraw, ImageFont
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--seed", type=int, default=1)
ap.add_argument("--mem", default="bank")
a = ap.parse_args()

HERE = os.path.dirname(os.path.abspath(__file__))
eps = [json.loads(l) for l in open(os.path.join(HERE, "suite/epm_v0.1_thor.jsonl"))]
e = next(x for x in eps if x["scene"] == "FloorPlan1" and x["seed"] == a.seed
         and x["delay"] == 6 and x["load"] == 1 and x["variant"] == "cancel_late")
spec = dict(e["spec"]); spec["chores"] = [tuple(c) for c in spec["chores"]]
it = spec["intentions"][0]
EV, CS = it["event_step"], it["cancel_step"]
TRIG = it["trigger_type"]

envh = ThorPMEnv(size=320)
frames, actions = [], []
orig_act = envh.act
def act_hook(action, arg=None):
    rec = orig_act(action, arg)
    frames.append(np.array(envh.c.last_event.frame))
    actions.append((rec["t"], action, arg, rec["ok"],
                    rec["trigger_visible"], rec["trigger_on"]))
    return rec
envh.act = act_hook
try:
    envh.reset(spec, scene="FloorPlan1")
    agents.run_mock_llm(envh, spec, mem=a.mem, window=6)
    adj = envh.adjudicate()
finally:
    envh.stop()

FW, FH, CAP = 320, 240, 46
COLS = 5
rows = (len(frames) + COLS - 1) // COLS
W, H = COLS * FW, rows * (FH + CAP) + 70
sheet = Image.new("RGB", (W, H), (18, 18, 22))
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 17)
    bigfont = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 24)
except OSError:
    font = bigfont = ImageFont.load_default()

verdict = "违规!" if adj["eac_strict"] else "清白"
draw.text((12, 8), f"一集连环画  考生:{a.mem}  剧本:第{EV}步世界打开{TRIG}(视野外) "
                   f"第{CS}步用户取消  判分:执行步={adj['exec_step']} -> EAC {verdict}",
          fill=(255, 255, 255), font=bigfont)

for i, (fr, (t, act, arg, ok, vis, on)) in enumerate(zip(frames, actions)):
    x, y = (i % COLS) * FW, 70 + (i // COLS) * (FH + CAP)
    img = Image.fromarray(fr).resize((FW, FH))
    sheet.paste(img, (x, y))
    label = f"t={t} {act} {arg or ''}"
    note, color = "", (150, 150, 150)
    if t == EV + 1 or (t == EV and i > 0):
        note, color = f"⚡世界刚打开{TRIG}—它没看见", (255, 165, 0)
    if t == CS + 1 or t == CS:
        note, color = "✋用户: 算了别管了(取消)", (80, 160, 255)
    if t == CS + 6:
        note, color = "…取消已滚出记忆窗口", (200, 120, 255)
    if vis and on:
        note, color = f"👁看见{TRIG}开着了!", (255, 230, 0)
    if act == "toggle_off" and arg == TRIG and ok:
        note, color = "🔴违规: 执行已取消的意图", (255, 60, 60)
        draw.rectangle([x + 2, y + 2, x + FW - 2, y + FH - 2],
                       outline=(255, 60, 60), width=5)
    draw.text((x + 6, y + FH + 4), label, fill=(230, 230, 230), font=font)
    if note:
        draw.text((x + 6, y + FH + 24), note, fill=color, font=font)

out = os.path.join(HERE, "results", f"storyboard_{a.mem}_s{a.seed}.png")
sheet.save(out)
print("saved", out, f"({len(frames)} frames)")
