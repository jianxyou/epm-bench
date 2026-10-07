# EPM-Bench: commission errors of deferred intentions in embodied LLM agents

Code, episode suite, results and paper sources for the AAMAS 2027 submission
*Remembering Not To: Commission Errors of Deferred Intentions in Embodied LLM Agents*.

An agent does chores in an AI2-THOR kitchen (or a Habitat apartment). At step 0 it is
given one deferred instruction ("if you ever notice the toaster is on, turn it off").
In the cancelled variants the user withdraws it a few steps later. The simulator then
switches the trigger on out of the agent's view. Nobody asks the agent anything; the
grader reads the simulator's event log. The independent variable is the memory
design: what is placed in front of the actor at each step, and who writes it.

## Layout

| Path | What it is |
|---|---|
| `env.py` | AI2-THOR environment: text observation, event engine (trigger switched on at the event step), cancel messages, world-state adjudication |
| `agents.py` | the LLM actor loop and all memory designs (`none`, `bank`, `retr`, `summ`, `rwim5` = RWIM-LEDGER, `sched2` = SCHED, ablations `sched1e` = SCHED-TAG, `retr2` = RETR-SCHED, `rwim4` = RWIM-NOTE); scripted oracle / patroller actors |
| `run_suite.py` | runs a policy over the frozen suite; one csv row per episode, per-episode dumps with `--dump-dir`; `--resume` skips finished episodes |
| `suite.py`, `tasks.py`, `suite/*.jsonl` | episode generator and the frozen suite (seeds, delays, loads, four matched variants); `suite/MANIFEST.json` has file hashes |
| `checkers.py` | per-intention checks used by adjudication |
| `pm_habitat.py`, `run_suite_hab.py`, `run_suite_habitat.py` | the Habitat tier (red-beacon instruction) |
| `audit_ledger_all.py` | audit of the self-kept ledgers (Section 5.3): fabricated entries per bookkeeper |
| `run_queue_*.sh` | the exact batch scripts that produced the result files (balance gate, two passes, resume) |
| `results/*.csv`, `results/*.json` | all per-episode results and the summary json files used by the paper (see the map below) |
| `paper_v02/make_stats.py` | aggregates the main cell into `paper_v02/stats.json` (Table 2 left half, Table 3, delay and held-out numbers) |
| `aamas2027/` | the paper: `main.tex`, `sections/01..07`, `refs.bib`, `figs/`, and the figure/table scripts |
| `REPORT.md` | the findings log, F1 to F56, with the numbers behind every claim and the dead ends |
| `NOTES_2026-08_design.md` | the original design notes (August) |

Design names in the code differ from the paper: `bank` = BANK, `retr` = RETR,
`summ` = SUMM, `rwim5` = RWIM-LEDGER, `sched2` = SCHED, `sched1e` = SCHED-TAG,
`retr2` = RETR-SCHED, `rwim4` = RWIM-NOTE, `rwim5@claude-sonnet-` = Sonnet-kept ledger.

## Map from the paper to the code and data

| In the paper | Script | Data |
|---|---|---|
| Table 2, one intention (EAC, EXEC, floor; 50 seeds) | `paper_v02/make_stats.py` -> `paper_v02/stats.json` | `results/llm_or_{gpt4omini,deepseek,llama,gemini}.csv` (cancel and live variants), `results/llm_or_*_ctrl2.csv` (control); frontier models `results/llm_or_sonnet5.csv`, `results/llm_or_gpt55.csv` |
| Table 2, six intentions (50 seeds) | `aamas2027/make_table_load6.py --write` -> `results/load6_table_s50.json` | `results/llm_or_*_load_v1obs.csv` (load 6 rows), per-intention verdicts in the dumps |
| Table 3, ablations | `paper_v02/stats.json` (keys `sched1e`, `retr2`, `rwim4`, `rwim5`, `rwim5@claude-sonnet-`) | `results/llm_or_gpt4omini.csv`, `results/llm_or_gemini.csv` |
| Figure 1 (overview) | `aamas2027/make_overview3.py` (icon version), `aamas2027/figs/fig_storyboard_thor.png` (real frames) | `aamas2027/figs/frames/` |
| Figure 2 (the six designs) | `aamas2027/make_designs_fig.py` | none |
| Load figure (Section 5.5) | `aamas2027/make_fig_load.py` (`--with-ledger` for the SCHED + RWIM-LEDGER version) | `results/llm_or_{gpt4omini,gemini}*.csv` at loads 1 to 6 |
| Ledger audit figure and Section 5.3 numbers | `aamas2027/make_figs_aamas.py` (`fig_ledger`), `audit_ledger_all.py` -> `results/audit_ledger_all.json` | dumps `results/or_*` (tarball) |
| Section 5.4 Habitat | `run_queue_habitat.sh` | `results/hab_or_gemini*.csv`, `results/hab_or_gpt4omini*.csv` |
| Section 5.4 full-context control | `run_queue_fullctx.sh` | `results/llm_or_{gpt4omini,gemini}_fullctx.csv` |
| Section 5.4 delay sweep, held-out kitchens | `paper_v02/make_stats.py` (`delay`, `heldout` keys) | `results/llm_or_*_delay.csv`, test-split rows in `results/llm_or_*.csv` |
| Section 5.5 exposure (seen / acted) | inline in REPORT F53/F55 | `results/load6_seen_s50.json` |
| Section 5.5 rescheduling | `run_queue_resched40.sh` | `results/llm_or_gpt4omini_resched.csv` |
| Section 3.5 oracle check, microwave artefact | REPORT F54 | `suite/epm_v0.1_thor.jsonl` |

Every number in the paper can be traced through `REPORT.md`: search for the finding
id (for example `F55`) to see the run, the file and the computation.

## Running an experiment

```bash
pip install ai2thor==5.0.0 openai anthropic numpy   # habitat-sim 0.3.1 for the Habitat tier
export OPENROUTER_API_KEY=...                      # or put the key in ~/.openrouter_key

# main cell: BANK and SCHED, cancel-early variant, 50 seeds, GPT-4o-mini
python3 run_suite.py --resume --split dev --delay 6 --load 1 --seeds 0:50 \
    --policies llm:bank,llm:sched2 --variant cancel_early \
    --model openai/gpt-4o-mini --out results/demo.csv --dump-dir results/or_demo

# six intentions (suite/epm_v0.1_thor_load6_s50.jsonl), all four variants
python3 run_suite.py --resume --suite suite/epm_v0.1_thor_load6_s50.jsonl --split dev \
    --delay 6 --load 6 --seeds 0:50 --policies llm:sched2 --variant live \
    --model google/gemini-2.5-flash-lite --out results/demo_load6.csv
```

Variants: `control`, `live`, `cancel_early`, `cancel_late`. Models are OpenRouter ids.
`--window` is the actor's context window in steps (default 6; `--window 40` gives the
full-context control). Each episode is seeded and replayable; `--resume` keys on
(policy, twin_group, variant).

## What is not in the repository

- `results/or_*/` : the per-episode dumps and step traces (about 630 MB). They are in
  the tarball `epm_traces_2026-10-07.tar.gz` shared alongside this repository; unpack
  it into `results/` to run `audit_ledger_all.py` and the per-intention computations.
- `data/` : Habitat scene assets; download with the Habitat tools.
- API keys. The code reads `OPENROUTER_API_KEY` / `ANTHROPIC_API_KEY` from the
  environment or a key file (`~/.openrouter_key`, `~/.anthropic_key`).
