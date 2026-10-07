#!/usr/bin/env python3
"""Analyze the 08-23 night batteries: headline tables + three figures.

Inputs (whatever exists is used):
  results/suite_thor_v01.csv      THOR battery over frozen suite
  results/suite_hab_v01.csv       Habitat battery over frozen suite
  results/hab_window_sweep.csv    Habitat EAC-vs-window (F8 parity)
  results/sched_geo_0823.csv      THOR mock grid n=48 (incl window arms)
  results/grading_records_0823.jsonl  three-regime grading records

Outputs: printed tables + results/fig_suite_headline.png,
fig_window_parity.png, fig_grading_ablation.png, and
results/night_0823_summary.json (all aggregates, for the morning report).
"""
import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
R = lambda *p: os.path.join(HERE, "results", *p)
SUMMARY = {}


def load(path):
    if not os.path.exists(path):
        return []
    return list(csv.DictReader(open(path)))


def frac(rows, key="executed"):
    if not rows:
        return None
    return sum(r[key] == "True" for r in rows) / len(rows)


def headline(rows, engine, delay, policies=None):
    out = {}
    hl = [r for r in rows if r["split"] == "dev" and r["delay"] == str(delay)
          and r.get("load", "1") == "1"]
    for pol in sorted({r["policy"] for r in hl}):
        if policies and pol not in policies:
            continue
        p = [r for r in hl if r["policy"] == pol]
        live = [r for r in p if r["variant"] == "live"]
        ctrl = [r for r in p if r["variant"] == "control"]
        canc = [r for r in p if r["variant"] in ("cancel_early", "cancel_late")]
        late = [r for r in p if r["variant"] == "cancel_late"]
        out[pol] = {
            "n_live": len(live), "EXEC": frac(live),
            "CTRL": frac(ctrl),
            "MEM": (None if not ctrl or not live
                    else frac(live) - frac(ctrl)),
            "EAC_any": frac(canc, "eac_strict"),
            "EAC_late": frac(late, "eac_strict"),
        }
    return out


def print_table(title, tab):
    print(f"\n== {title} ==")
    print(f"{'policy':18s} {'n':>4s} {'EXEC':>6s} {'CTRL':>6s} {'MEM':>6s} "
          f"{'EAC':>6s} {'EAC_late':>8s}")
    for pol, d in sorted(tab.items()):
        f = lambda v: "   -  " if v is None else f"{100*v:5.1f}%"
        print(f"{pol:18s} {d['n_live']:4d} {f(d['EXEC'])} {f(d['CTRL'])} "
              f"{f(d['MEM'])} {f(d['EAC_any'])} {f(d['EAC_late']):>8s}")


def main():
    thor = load(R("suite_thor_v01.csv"))
    hab = load(R("suite_hab_v01.csv"))
    if thor:
        t = headline(thor, "thor", 6)
        print_table("THOR dev delay=6 load=1 (frozen suite v0.1)", t)
        SUMMARY["thor_headline"] = t
        # test-split generalization
        ts = [r for r in thor if r["split"] == "test"]
        gen = {}
        for pol in sorted({r["policy"] for r in ts}):
            p = [r for r in ts if r["policy"] == pol]
            live = [r for r in p if r["variant"] == "live"]
            late = [r for r in p if r["variant"] == "cancel_late"]
            gen[pol] = {"n_live": len(live), "EXEC": frac(live),
                        "CTRL": None, "MEM": None, "EAC_any": None,
                        "EAC_late": frac(late, "eac_strict")}
        print_table("THOR test split (FloorPlan2/3/4, unseen scenes)", gen)
        SUMMARY["thor_test"] = gen
    if hab:
        h = headline(hab, "habitat", 10)
        print_table("HABITAT dev delay=10 (frozen suite v0.1)", h)
        SUMMARY["hab_headline"] = h
        ts = [r for r in hab if r["split"] == "test"]
        gen = {}
        for pol in sorted({r["policy"] for r in ts}):
            p = [r for r in ts if r["policy"] == pol]
            live = [r for r in p if r["variant"] == "live"]
            late = [r for r in p if r["variant"] == "cancel_late"]
            gen[pol] = {"n_live": len(live), "EXEC": frac(live),
                        "CTRL": None, "MEM": None, "EAC_any": None,
                        "EAC_late": frac(late, "eac_strict")}
        print_table("HABITAT test split (castle, unseen scene)", gen)
        SUMMARY["hab_test"] = gen

    # ---- window parity (F8 cross-engine) ----
    sweep_hab = load(R("hab_window_sweep.csv"))
    geo = load(R("sched_geo_0823.csv"))
    parity = {"habitat": {}, "thor_mock": {}}
    for w in sorted({r["window"] for r in sweep_hab if r.get("window")},
                    key=lambda x: int(x)):
        for pol in ("mockllm-bank", "mockllm-rwim", "mockllm-sched"):
            rows = [r for r in sweep_hab if r["window"] == w
                    and r["policy"] == pol]
            if rows:
                parity["habitat"].setdefault(pol, {})[int(w)] = \
                    frac(rows, "eac_strict")
    for w in sorted({r["window"] for r in geo}, key=lambda x: int(x)):
        for pol in ("bank", "rrn"):
            rows = [r for r in geo if r["window"] == w and r["policy"] == pol
                    and r["cancel"] in ("early", "late") and r["load"] == "1"]
            if rows:
                parity["thor_mock"].setdefault(pol, {})[int(w)] = \
                    frac(rows, "eac_strict")
    if any(parity.values()):
        print("\n== EAC vs window (cancel arms pooled) ==")
        for eng, d in parity.items():
            for pol, curve in d.items():
                pts = " ".join(f"w{w}:{100*v:.0f}%"
                               for w, v in sorted(curve.items()))
                print(f"  {eng:10s} {pol:14s} {pts}")
        SUMMARY["window_parity"] = parity

    # ---- grading ablation ----
    # prefer the b-file: probes re-aligned to the actor's full final-step
    # information (window text + that step's injected notes)
    gpath = (R("grading_records_0823b.jsonl")
             if os.path.exists(R("grading_records_0823b.jsonl"))
             else R("grading_records_0823.jsonl"))
    if os.path.exists(gpath):
        recs = [json.loads(x) for x in open(gpath)]
        # cancelled intentions only, the termination question
        canc = [r for r in recs if r["cancelled"]]
        viol = [r for r in canc if r["world_eac"]]
        clean = [r for r in canc if not r["world_eac"]]
        # A grading regime "passes" the agent on termination if it concludes
        # the agent handled the cancellation correctly:
        #   QA: agent can answer "it was cancelled" at episode end
        #   selection: agent would not act on it at episode end
        #   world-state: no execution after cancellation (ground truth)
        qa_pass_on_viol = (sum(r["qa_knows_cancel_end"] for r in viol)
                          / len(viol)) if viol else None
        sel_pass_on_viol = (sum(not r["sel_would_act_end"] for r in viol)
                           / len(viol)) if viol else None
        qa_fail_on_clean = (sum(not r["qa_knows_cancel_end"] for r in clean)
                           / len(clean)) if clean else None
        g = {"n_cancelled": len(canc), "n_world_violations": len(viol),
             "qa_passes_violators": qa_pass_on_viol,
             "selection_passes_violators": sel_pass_on_viol,
             "qa_fails_clean": qa_fail_on_clean}
        print("\n== Grading-regime ablation (same episodes, three graders) ==")
        for k, v in g.items():
            print(f"  {k}: {v if isinstance(v, int) else (f'{100*v:.1f}%' if v is not None else '-')}")
        SUMMARY["grading_ablation"] = g

    with open(R("night_0823_summary.json"), "w") as f:
        json.dump(SUMMARY, f, indent=1)
    print("\nsummary -> results/night_0823_summary.json")

    # ---- figures ----
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib unavailable; skipping figures")
        return

    if "thor_headline" in SUMMARY or "hab_headline" in SUMMARY:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
        for ax, (name, key) in zip(axes, [("AI2-THOR (delay 6)",
                                           "thor_headline"),
                                          ("Habitat (delay 10)",
                                           "hab_headline")]):
            tab = SUMMARY.get(key, {})
            pols = [p for p in tab if tab[p]["EXEC"] is not None]
            pols.sort(key=lambda p: -(tab[p]["EXEC"] or 0))
            x = range(len(pols))
            ax.bar([i - 0.2 for i in x],
                   [100 * (tab[p]["EXEC"] or 0) for p in pols], 0.4,
                   label="EXEC (live)")
            ax.bar([i + 0.2 for i in x],
                   [100 * (tab[p]["EAC_any"] or 0) for p in pols], 0.4,
                   label="EAC (cancelled)", color="firebrick")
            ax.set_xticks(list(x))
            ax.set_xticklabels(pols, rotation=40, ha="right", fontsize=8)
            ax.set_title(name)
            ax.set_ylim(0, 105)
        axes[0].set_ylabel("%")
        axes[0].legend()
        fig.suptitle("EPM-Bench v0.1 frozen suite: execution vs commission")
        fig.tight_layout()
        fig.savefig(R("fig_suite_headline.png"), dpi=150)
        print("fig -> results/fig_suite_headline.png")

    if SUMMARY.get("window_parity"):
        fig, ax = plt.subplots(figsize=(6.5, 4))
        styles = {("habitat", "mockllm-bank"): ("o-", "tab:red",
                                                "Habitat bank"),
                  ("habitat", "mockllm-rwim"): ("s--", "tab:orange",
                                                "Habitat rwim"),
                  ("habitat", "mockllm-sched"): ("^-", "tab:green",
                                                 "Habitat sched"),
                  ("thor_mock", "bank"): ("o:", "darkred", "THOR-mock bank"),
                  ("thor_mock", "rrn"): ("^:", "darkgreen", "THOR-mock rrn")}
        for (eng, pol), curve in [((e, p), c) for e, d in
                                  SUMMARY["window_parity"].items()
                                  for p, c in d.items()]:
            st = styles.get((eng, pol))
            if not st or not curve:
                continue
            ws = sorted(curve)
            ax.plot(ws, [100 * curve[w] for w in ws], st[0], color=st[1],
                    label=st[2])
        ax.set_xlabel("context window (transcript lines)")
        ax.set_ylabel("executed-after-cancel %")
        ax.set_title("Cancel-retention vs window: cross-engine parity")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(R("fig_window_parity.png"), dpi=150)
        print("fig -> results/fig_window_parity.png")

    if SUMMARY.get("grading_ablation"):
        g = SUMMARY["grading_ablation"]
        fig, ax = plt.subplots(figsize=(5.5, 4))
        bars = [("world-state\n(ground truth)", 0.0, "tab:gray"),
                ("QA-style\n(quiz at end)", g["qa_passes_violators"] or 0,
                 "tab:blue"),
                ("selection-style\n(menu at end)",
                 g["selection_passes_violators"] or 0, "tab:orange")]
        ax.bar([b[0] for b in bars], [100 * b[1] for b in bars],
               color=[b[2] for b in bars])
        ax.set_ylabel("% of world-state violators GRADED AS PASSING")
        ax.set_title(f"Same {g['n_world_violations']} violation episodes, "
                     f"three graders")
        fig.tight_layout()
        fig.savefig(R("fig_grading_ablation.png"), dpi=150)
        print("fig -> results/fig_grading_ablation.png")


if __name__ == "__main__":
    main()
