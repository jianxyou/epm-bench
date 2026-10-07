#!/usr/bin/env python3
"""Cost estimate for the LLM solidification grid (spec §8), from measured
tokens/episode in llm_real.csv (Haiku, THOR tier, 08-06 pilot).

Run: python3 estimate_llm_cost.py
"""
# measured mean api_tokens per episode (in+out), THOR privileged-text tier
TOK = {"none": 19_000, "bank": 59_000, "rwim": 84_000, "sched": 20_000}
HAB_TOK = {"none": 12_000, "bank": 30_000, "sched": 15_000}  # est: 60 steps,
# leaner obs text than THOR; refresh after 10-episode calibration run
RGB_MULT = 4.0          # image tokens; refresh after calibration
PRICE = {"haiku": 1.5e-6, "sonnet": 6.0e-6}   # blended $/token (in-heavy mix)

ARMS = [
    # (label, model, engine, mems, n_variants, n_seeds, mult)
    ("THOR headline 4 mems x 4 variants x n=50", "haiku", "thor",
     ["none", "bank", "rwim", "sched"], 4, 50, 1.0),
    ("THOR load 2/3: bank+sched x 2 var x n=25 x 2 loads", "haiku", "thor",
     ["bank", "sched", "bank", "sched"], 2, 25, 1.0),
    ("THOR RGB tier: bank+sched x 2 var x n=25", "haiku", "thor",
     ["bank", "sched"], 2, 25, RGB_MULT),
    ("Habitat: 3 mems x 2 var x n=50", "haiku", "habitat",
     ["none", "bank", "sched"], 2, 50, 1.0),
    ("Sonnet replication: 3 mems x 2 var x n=25", "sonnet", "thor",
     ["none", "bank", "sched"], 2, 25, 1.0),
]

total = 0.0
print(f"{'arm':55s} {'episodes':>8s} {'Mtok':>7s} {'cost':>8s}")
for label, model, engine, mems, n_var, n_seeds, mult in ARMS:
    tok_tab = TOK if engine == "thor" else HAB_TOK
    eps = len(mems) * n_var * n_seeds
    mtok = sum(tok_tab[m] * n_var * n_seeds * mult for m in mems) / 1e6
    cost = mtok * 1e6 * PRICE[model]
    total += cost
    print(f"{label:55s} {eps:8d} {mtok:7.1f} ${cost:7.2f}")
print(f"{'TOTAL':55s} {'':8s} {'':7s} ${total:7.2f}")
print("\nNotes: prices blended estimates; rerun the 10-episode calibration "
      "arm first and refresh TOK/HAB_TOK/RGB_MULT before trusting the total. "
      "Fits the ~$150 budget from the spec.")
