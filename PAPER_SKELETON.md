# ICLR 2027 Paper Skeleton — "EPM-Bench" (working title, v0.1 night of 08-15)

Target: abstract 9/18, paper 9/25. Go/no-go 9/5 after advisor meeting.

## Title candidates
1. EPM-Bench: Prospective Memory for Embodied Agents, Adjudicated from World State
2. Remember to Act, Remember to Stop: Benchmarking the Intention Lifecycle in Embodied Agents
3. The Kettle Test: Deferred Intentions and Their Cancellation in Embodied Agents

## Abstract skeleton (6 sentences)
1. Hook: tell an agent "when you notice the kettle boiling, turn it off" — then cancel it. Will it still act?
2. Gap: agent memory research is retrospective; no benchmark gives an embodied agent a deferred instruction and adjudicates the full lifecycle from world state; no prior work isolates executed-after-cancel.
3. We introduce EPM-Bench: dual-simulator (AI2-THOR + Habitat), procedurally generated episodes, event engine firing triggers out of view, matched control/live/cancelled triples, deterministic checkers.
4. Findings: commission errors are architectural — naive stores execute up to 60% of cancelled intentions; a typed store with mechanical strikethrough eliminates them at 1/3 cost; the ranking is invariant across model scale and simulators.
5. Mechanism: a mock-actor decomposition separates information starvation from attention tax; scheduling governs a three-way cost/execution/compliance trade-off that no fixed policy wins, and load collapses every policy tested.
6. Release: environments, generator, checkers, traces; PM as a measurable, safety-relevant capability axis.

## Sections
1. **Intro** — kettle story; lifecycle figure; contributions (benchmark, EAC metric, mechanism findings, mock methodology).
2. **Related work** — compress survey Secs 5-9: PM benchmarks (TriggerBench/PM-Bench: text, selection-graded), timing cluster (Gaia2/SentinelBench/SimuHome), embodied memory (FindingDory/MEMENTO/WorldLines: all retrospective), termination neighbors (VIGIL completion-half; Revisable in-flight; ProEvent record-level). One paragraph psychology anchor (multiprocess framework, commission errors, Virtual Week).
3. **Benchmark** — from BENCHMARK_SPEC.md: schema, axes, metrics (EAC headline), validity probes (deaf agent, control twins), adjudication philosophy (no judge).
4. **Experiments**
   - 4.1 Scripted frontier: cost-compliance, delay dose-response, focality, load, cross-sim monitoring collapse, adaptive dominance.
   - 4.2 LLM tier: five memory policies × two simulators × two model scales; commission headline; failure taxonomy (chatty coroutine, semantic capture, early clock-out) with trace excerpts.
   - 4.3 Mechanism: sched_geometry — mechanical floors vs LLM observed (information vs attention decomposition); window×cancel-retention interaction.
   - 4.4 Perception tier: RGB tax, ranking preserved.
5. **Analysis** — what EAC correlates with (schedule sparsity, cancel-to-trigger gap, window); why menu/QA grading cannot see it (mini-ablation: same episodes graded three ways?  <- nice addition if time).
6. **Limitations & safety** — n, model families, single-user intentions; commission as safety surface (sleeper mirror, one paragraph).

## Figures plan (have / need)
- F1 lifecycle + benchmark schematic (have TikZ, redraw prettier)  
- F2 dual-simulator headline (have: fig_llm_real)
- F3 model scale invariance (have: fig_model_scale)
- F4 three-way trade-off frontier (have: fig_frontier + tonight's sched_geometry)
- F5 mechanism decomposition (tonight: mechanical floor vs Haiku observed)
- F6 load collapse (have: fig_load_llm)
- F7 failure taxonomy with trace snippets (from results/traces)

## Risks
- n small → solidification list (spec §8) before submission
- "just a testbed" review → lean on checker rigor + validity probes + mechanism
- concurrent work (watchlist: NormAct, WorldLines follow-ups) → weekly radar
