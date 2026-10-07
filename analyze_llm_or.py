#!/usr/bin/env python3
"""Multi-model LLM-tier table from results/llm_or_*.csv (protocol v2).
Usage: python3 analyze_llm_or.py [--md]
Rows: model x memory policy. Cols: EXEC(live) CTRL MEM EAC(early) EAC(late)
chores/ep tokens/ep $/ep. Price table: OpenRouter $/M (prompt, completion).
"""
import csv, glob, os, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
PRICE = {  # $/M tokens (prompt, completion); ~92% of tokens are prompt
    "openai/gpt-4o-mini": (0.15, 0.60),
    "deepseek/deepseek-chat": (0.26, 1.03),
    "meta-llama/llama-3.3-70b-instruct": (0.10, 0.32),
    "qwen/qwen3-32b": (0.08, 0.28),
    "google/gemini-2.5-flash-lite": (0.10, 0.40),
    "anthropic/claude-haiku-4.5": (1.00, 5.00),
}
FILE2MODEL = {
    "llm_or_gpt4omini": "openai/gpt-4o-mini",
    "llm_or_gpt4omini_schedv2": "openai/gpt-4o-mini",
    "llm_or_deepseek": "deepseek/deepseek-chat",
    "llm_or_deepseek_sched": "deepseek/deepseek-chat",
    "llm_or_llama": "meta-llama/llama-3.3-70b-instruct",
    "llm_or_qwen": "qwen/qwen3-32b",
}


def load():
    rows = []
    for path in sorted(glob.glob(os.path.join(HERE, "results", "llm_or_*.csv"))):
        stem = os.path.basename(path)[:-4]
        model = FILE2MODEL.get(stem, stem)
        # sched v1 (old wording) lives in the first gpt4omini file; v2 in its own
        for r in csv.DictReader(open(path)):
            r["model"] = model
            rows.append(r)
    # keep the first occurrence per cell (a duplicate launch once appended
    # two extra rows to a CSV that another process was still writing)
    seen, out = set(), []
    for r in rows:
        k = (r["model"], r["policy"], r["variant"], r["seed"])
        if k in seen:
            continue
        seen.add(k); out.append(r)
    return out


def pct(xs):
    return f"{100*sum(xs)/len(xs):5.1f}" if xs else "  -  "


def main():
    rows = load()
    g = collections.defaultdict(list)
    for r in rows:
        g[(r["model"], r["policy"], r["variant"])].append(r)
    models = sorted({r["model"] for r in rows})
    pols = ["llm-none", "llm-bank", "llm-sched", "llm-sched1", "llm-rwim"]
    md = "--md" in sys.argv
    hdr = ["model", "policy", "n", "EXEC", "CTRL", "MEM", "EAC-early",
           "EAC-late", "chores", "tok/ep", "$/ep"]
    if md:
        print("| " + " | ".join(hdr) + " |"); print("|" + "---|" * len(hdr))
    else:
        print(f"{'model':<34}{'policy':<11}{'n':>3} {'EXEC':>6} {'CTRL':>6} "
              f"{'MEM':>6} {'EACe':>6} {'EACl':>6} {'chores':>7} {'tok/ep':>8} {'$/ep':>7}")
    total_cost = 0.0
    for m in models:
        for p in pols:
            live = g[(m, p, "live")]; ctrl = g[(m, p, "control")]
            ce = g[(m, p, "cancel_early")]; cl = g[(m, p, "cancel_late")]
            allr = live + ctrl + ce + cl
            if not allr:
                continue
            ex = [r["executed"] == "True" for r in live]
            ct = [bool(r["exec_step"]) for r in ctrl]
            mem = (f"{(sum(ex)/len(ex)-sum(ct)/len(ct))*100:5.1f}"
                   if ex and ct else "  -  ")
            eae = [r["eac_strict"] == "True" for r in ce]
            eal = [r["eac_strict"] == "True" for r in cl]
            ch = sum(int(r["chores_done"]) for r in allr) / len(allr)
            tk = sum(int(r["api_tokens"]) for r in allr) / len(allr)
            pi, po = PRICE.get(m, (0, 0))
            cost = tk * (0.92 * pi + 0.08 * po) / 1e6
            total_cost += cost * len(allr)
            vals = [m, p, str(len(live)), pct(ex), pct(ct), mem, pct(eae),
                    pct(eal), f"{ch:.1f}", f"{tk:.0f}", f"{cost:.4f}"]
            if md:
                print("| " + " | ".join(vals) + " |")
            else:
                print(f"{m:<34}{p:<11}{len(live):>3} {pct(ex):>6} {pct(ct):>6} "
                      f"{mem:>6} {pct(eae):>6} {pct(eal):>6} {ch:>7.1f} "
                      f"{tk:>8.0f} {cost:>7.4f}")
    print(f"\n{len(rows)} episodes, est. spend ${total_cost:.2f}")


if __name__ == "__main__":
    main()
