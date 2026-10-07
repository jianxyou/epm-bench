#!/usr/bin/env python3
"""Analyze sched_geometry.csv -> summary table + fig_sched_geometry.png"""
import csv
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "results", "sched_geometry.csv")
FIG = os.path.join(HERE, "results", "fig_sched_geometry.png")

rows = list(csv.DictReader(open(CSV)))
for r in rows:
    r["load"] = int(r["load"])
    r["executed_frac"] = float(r["executed_frac"]) if r["executed_frac"] else None
    r["eac"] = 1.0 if r["eac_strict"] == "True" else 0.0
    r["notes"] = int(r["notes_injected"])
    r["chores"] = int(r["chores_done"])

POLS = ["bank", "every5", "rr", "rrn", "sight"]
LOADS = sorted({r["load"] for r in rows})


def cell(pol, load, cancel):
    return [r for r in rows if r["policy"] == pol and r["load"] == load
            and r["cancel"] == cancel]


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")


print(f"{'pol':8s} {'load':4s} | {'EXEC(none)':>10s} {'EAC(early)':>10s} "
      f"{'EAC(late)':>9s} {'notes/ep':>8s} {'chores':>6s} | n")
table = {}
for pol in POLS:
    for load in LOADS:
        exec_none = mean([r["executed_frac"] for r in cell(pol, load, "none")])
        eac_e = mean([r["eac"] for r in cell(pol, load, "early")])
        eac_l = mean([r["eac"] for r in cell(pol, load, "late")])
        notes = mean([r["notes"] for r in rows
                      if r["policy"] == pol and r["load"] == load])
        chores = mean([r["chores"] for r in rows
                       if r["policy"] == pol and r["load"] == load])
        n = len(cell(pol, load, "none"))
        table[(pol, load)] = (exec_none, eac_e, eac_l, notes, chores)
        print(f"{pol:8s} {load:<4d} | {exec_none:10.2f} {eac_e:10.2f} "
              f"{eac_l:9.2f} {notes:8.1f} {chores:6.1f} | {n}")

fig, axes = plt.subplots(1, 3, figsize=(13, 4))
colors = {"bank": "#d62728", "every5": "#ff7f0e", "rr": "#1f77b4",
          "rrn": "#2ca02c", "sight": "#9467bd"}
for pol in POLS:
    xs = LOADS
    axes[0].plot(xs, [table[(pol, l)][0] for l in xs], "o-",
                 color=colors[pol], label=pol)
    axes[1].plot(xs, [table[(pol, l)][1] for l in xs], "o-",
                 color=colors[pol], label=pol)
    axes[2].plot([table[(pol, l)][3] for l in xs],
                 [table[(pol, l)][0] for l in xs], "o-",
                 color=colors[pol], label=pol)
axes[0].set_xlabel("intention load"); axes[0].set_ylabel("EXEC (live, no-cancel)")
axes[0].set_title("Execution vs load (mechanical)"); axes[0].set_ylim(-0.05, 1.05)
axes[1].set_xlabel("intention load"); axes[1].set_ylabel("EAC strict (early cancel)")
axes[1].set_title("Commission vs load"); axes[1].set_ylim(-0.05, 1.05)
axes[2].set_xlabel("notes injected / episode (cost)")
axes[2].set_ylabel("EXEC"); axes[2].set_title("Cost-execution frontier")
for ax in axes:
    ax.grid(alpha=0.3); ax.legend(fontsize=8)
fig.suptitle("Scheduling geometry, mock actor (information floor, no attention)",
             fontsize=11)
fig.tight_layout()
fig.savefig(FIG, dpi=140)
print("fig ->", FIG)
