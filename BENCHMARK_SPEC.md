# EPM-Bench: Embodied Prospective Memory Benchmark — Formal Spec (v0.1, night of 08-15)

Feeds ICLR paper Section 3. Grounded in the existing infra (env.py / tasks.py /
pm_habitat.py); everything listed either exists or is one flag away.

## 1. Design goals (each traces to a survey claim)

1. **Full lifecycle in one episode**: acquisition (mid-task deferred instruction),
   retention (interference from ongoing chores), execution (trigger fires out of
   view; noticing must be earned), termination (matched cancelled variants;
   exactly-once completion).
2. **World-state adjudication only.** Success/violation computed from simulator
   event logs by deterministic code. No LLM judge anywhere. Checkers ship with
   the benchmark (ABC lesson: judge bugs produced up to 100% relative error).
3. **Isolate memory from common sense.** Every seed has a no-instruction control
   twin; report memory contribution = treatment − control. Habitat beacon
   triggers (arbitrary marker + declare) have no common-sense confound by design.
4. **Separate noticing from acting.** Visibility instrumented per step
   (FOV + distance + occlusion); every failure classified encoding / noticing /
   execution / termination.

## 2. Episode schema

```
episode := {
  seed, scene, engine ∈ {thor, habitat},
  chores: [(object, receptacle) × n_chores],          # ongoing task
  intentions: [
    { instruction,                                     # "when you see X on, turn it off"
      trigger: {type ∈ {event, time, location}, object/step/zone},
      event_step,                                      # world fires it out of view
      focality ∈ {on-route, off-route},
      cancel_step | null,                              # revocation delivery time
    } × load
  ],
  variant ∈ {control, live, cancelled},                # matched triple per seed
  perception ∈ {privileged-text, rgb},
}
```

## 3. Difficulty axes (all validated in pilot)

| Axis | Levels | Pilot evidence |
|---|---|---|
| delay (event_step) | 3 / 6 / 10 / 14 | dose-response 91.7→25% (scripted) |
| load (n intentions) | 1 / 2 / 3 / 5 | 95.8/83.3/54.2 scripted; sched 90/30/20 LLM |
| focality | on/off chore route | 88.5 vs 40% |
| cancel timing | early / late / none | eac_strict validated by deaf probe |
| scene scale | kitchen / apartment | monitoring value collapses +8.3→+0.0 |
| perception | text / RGB | ~30-pt tax, ranking preserved |

## 4. Metrics (per condition, mean over seeds)

- **EXEC**: fraction of live intentions executed (arrive-and-declare in Habitat;
  state-change in THOR). Exactly-once: re-execution counts as violation.
- **EAC (headline)**: executed-after-cancel, strict — execution strictly after
  revocation delivery. The number no prior work reports.
- **MEM**: EXEC(live) − EXEC(control): memory contribution net of common sense.
- **NOTICE**: first-visible-step vs exec-step decomposition; failure attribution
  shares (never-visible / visible-unnoticed / noticed-unexecuted).
- **COST**: steps, tokens, notes injected; chores completed (opportunity cost).
- Frontier plots: COST × EXEC × EAC per policy (the three-way trade-off).

## 5. Baselines (all implemented)

Scripted: oracle / negligent / patroller(k) / opportunistic / adaptive
(reset-on-sight) / deaf (validity probe).
LLM memory policies: none / bank (always-inject) / naive coroutine (RWIM-style)
/ scoped coroutine / typed store + mechanical scheduler (sched).
Mock actor: window-bounded rule reader — separates information starvation from
attention tax (see sched_geometry study).

## 6. Validity probes (release with benchmark)

- **Deaf agent**: cannot receive cancellations; its EAC must equal its EXEC —
  calibrates that EAC measures compliance, not ability.
- **No-intention control**: measures common-sense floor per scene/trigger.
- **Determinism check**: same seed+policy → identical event log hash.
- **Mock replication**: any mechanical claim must reproduce on the rule actor
  before being attributed to the model.

## 7. Splits & release — FROZEN as of 08-23 (suite/)

- `epm_v0.1_thor.jsonl` 6000 episodes: dev FloorPlan1 seeds 0-99 ×
  delays{3,6,10,14} × loads{1,2,3} × 4 variants; test FloorPlan2/3/4
  seeds 100-199 at default difficulty. `epm_v0.1_habitat.jsonl` 1564:
  dev apartment_1 × delays{6,10,14}; test skokloster-castle (36 castle
  seeds unsatisfiable, skipped at generation).
- 1891 matched twin groups (control / live / cancel_early / cancel_late);
  control specs carry `has_intention: false` — memory policies must inject
  nothing for them (fabricated-intention contamination caught 08-23).
- `MANIFEST.json`: SHA256 per file + full design record.
- `checkers.py`: engine-agnostic adjudication module, 8 synthetic-log unit
  tests; per-intention failure attribution (never_visible / seen_not_executed
  / executed).
- Validity status: oracle audits green both engines; determinism probe
  bit-identical (8 episodes × 2 runs); deaf calibration exact on early-cancel
  arms both engines.
- KNOWN v0.1 LIMITATION: THOR late-cancel (cs = delay+2) coincides with the
  fastest scripted response step, so strict-EAC on that one arm is
  definitionally 0 for step-8-capable agents (deaf shows 47/50
  executed-after-cancel loose vs 0 strict). Habitat (+4) unaffected.
  v0.2: enforce cancel-to-fastest-exec gap ≥ 1 step.
- Habitat tier is single-intention in v0.1; multi-intention load lives in the
  THOR tier + sched_geometry mock battery.

## 8. Solidification status (08-23 night)

DONE zero-API: scripted+mock batteries on the frozen suite (THOR n=50
headline, n=24 axes+test; Habitat n=49 headline, castle test), window-parity
sweep, three-regime grading ablation, n=48 sched-geometry grid.
REMAINS (needs working API key — current key 401-invalid, needs REPLACEMENT
not recharge): `llm_grid_0823.sh` runs the whole LLM program in one command;
`estimate_llm_cost.py` prices it at ~$128 (fits $150): THOR headline n=50 ×
4 mems, load curve, RGB tier, Habitat n=50, Sonnet replication. OpenRouter
multi-family still TODO (needs an agents.py adapter). Prompt ablations
(sched "do not say done") unchanged.
