# Prospective Memory in Embodied Worlds: Overnight Pilot Report

*2026-08-06, ~5400 seeded episodes across two simulators (AI2-THOR, habitat-sim).
All agents scripted or rule-based (zero API). Companion figures in `results/`.
Headline results re-verified on held-out seeds (n=73–100 per cell): triptych
THOR 0 / 90.8±6.5 (39.5±11.0 violations) / 90.8 (0); Habitat 0 / 74.0±10.1
(63.0±11.1) / 74.0 (0).*

## One paragraph

We built the first execution-graded prospective-memory testbed in 3D worlds:
deferred instructions ("if you ever see X, do Y") injected before their trigger,
a seeded event engine that changes the world out of view, per-step visibility
instrumentation, and world-state adjudication with matched cancellation mirrors.
Across ~4000 episodes, reference agents reproduce the signature phenomena of
human prospective memory — monitoring cost, delay decay, intention load,
cue focality — and a window-bounded rule actor mechanically demonstrates the
project's central thesis: **an agent without an external store forgets the
intention; an agent with a naively injected store forgets its revocation; only
scheduled memory delivery preserves both** (fig_triptych.png).

## Instruments

- **Kitchen tier (AI2-THOR)**: object-state triggers (toaster/faucet toggled on
  behind the agent's back), execution = the device is actually off. Chores =
  pick-and-place. 10 scenes audited solvable (oracle 100%).
- **Apartment tier (habitat-sim)**: multi-room navigation world; trigger = a
  marker appearing out of view; execution = arrive AND declare. Chores =
  waypoint errands. Geometric visibility (FOV + distance + line-of-sight).
- Metrics: executed / executed_frac, first_visible_step (noticing), chores_done
  (foreground cost), steps, and **eac_strict** — executed strictly after a
  cancellation was delivered, validated by deaf-agent probes (75–100% caught;
  honest agents 0%).

## Findings

**F1. Monitoring has a price, and space sets the price** (fig_frontier,
fig_crosssim). Kitchen: patrolling every 2–12 steps trades 95.8→70.8% execution
against 0.8→3.8 chores. Apartment: periodic patrolling is *strictly dominated*
by doing nothing extra (79.2% vs 79.2% execution at 4x the chore cost) — one
glance covers a kitchen, but only one room of an apartment.

**F2. Where to look beats how often** (ladder.csv). Coverage-greedy vantage
selection lifts patrol execution 70.8→95.8% at identical chore cost. Monitoring
in large spaces is a *placement* problem before it is a *frequency* problem.

**F3. Free monitoring exists only in slack** . Under heavy workload,
monitor-when-idle equals pure incidental noticing; under light workload it adds
+46 points at zero foreground cost (83.3% vs 37.5%).

**F4. Incidental noticing is real but decays** (fig_delay). With no monitoring
at all, execution falls 91.7→25.0% (kitchen) and 79→67% (apartment) as the
event moves later; disciplined monitoring degrades far more slowly.

**F5. Intention load degrades everything** (fig_load). Carrying 1/2/3
simultaneous intentions: 95.8/83.3/54.2% (patroller), 87.5/70.8/33.3%
(opportunistic), with foreground output flat — the psychology intention-load
effect, mechanically.

**F6. Focality emerges and is controllable** (fig_focality). The same cue on
vs off the errand path: 88.5 vs 40% (coffee machine), 54.2 vs 0% (microwave);
ambient placement adds a second component (counter-top toaster: 84% while
never on-route). Salience × difficulty interact: perception radius only
matters at hard delays (54→71% at delay 14).

**F7. The memory-policy triptych** (fig_triptych, fig_window3d). A rule actor
that can only use text inside its context window: no store → 0% (the briefing
evicts; window size is a dose: 0/0/29/63/67% for w=3..48); always-injected
store → 75% execution but **58.3% executed-after-cancel** (the store pins the
intention while the revocation scrolls away); coroutine-scheduled injection →
75% execution, **0%** violations.

**F8. The revocation evicts too** (revoke_sweep.csv). The always-injected
store's executed-after-cancel rate falls monotonically with window size
(70.8 → 0% for w=3..48): a big enough window keeps the cancel visible. Mirror
image of F7's intention-eviction curve — **the window evicts whatever is not
pinned, the intention or its revocation**. Together they are the complete
mechanical argument for scheduled memory.

**F9. A scale law for monitoring** (fig_scale.png). Patrolling's net benefit
over incidental noticing collapses monotonically with spatial scale *within a
single engine*: tiny room +10.6 pp, (THOR kitchen +8.3), apartment +0.0,
castle hall −16.7 — where even coverage-greedy placement loses, because
perception radius becomes the binding constraint. No monitoring strategy is
universal: workload, placement, priors, and scale each have a regime.

**F10. One line of scheduling beats every fixed schedule** (fig_adaptive.png).
An adaptive patroller that resets its monitoring clock on incidental sightings
(patrol only if the cue is k steps unseen) collapses the whole fixed-k frontier
to a single dominating point (95.8% execution, 3.79/6 chores, insensitive to k).
The value of a monitoring scheduler comes from consuming information that is
already free. The cross-engine mock triptych (THOR: 0 / 87.5+41.7 / 87.5+0;
Habitat: 0 / 75+58.3 / 75+0) shows the memory-policy thesis is
engine-independent.

**F11. Real-LLM five-policy showdown** (fig_llm_real.png; Haiku, n=10/arm).
Predictions from the mock actor held and sharpened: no store 40% execution
(a common-sense floor: passing a burning toaster, Haiku sometimes just fixes
it); always-injected store 100% execution but **70% executed-after-cancel**;
and two LLM-coroutine variants FAILED in structurally distinct ways captured
by the traces: the naive coroutine emits 28-35 notes per 40 steps, all
present-tense chore micromanagement, never the deferred intention (10%);
the scoped coroutine relabels chores as "deferred intentions" and still leaves
the real one unguarded (30%); actors also clock out ("done") with obligations
open. A typed intention registry with mechanical scheduled resurfacing
(reminder every 6 steps, cancellation announced immediately) restores 100%
execution with violations at the common-sense floor (10%) at one third of the
always-inject token cost. Storing is easy; scheduling is the science; and the
scheduling cannot be naively delegated to an LLM.

**F12. Cross-simulator real-LLM replication with a clean control**
(fig_llm_real.png right panel). A no-intention control puts THOR's
common-sense floor at 30% (Haiku fixes a burning toaster it was never asked
about), so the no-store arm's 40% contains only ~10 points of actual memory.
Habitat's beacon carries no common-sense meaning, isolating memory perfectly:
no store 0%, always-injected store 60% execution with 60% post-cancel
violations, typed+scheduled store 60% with **zero** violations (60% = the
multi-room visibility ceiling). The storing-vs-scheduling thesis now holds at
three evidence levels: mock mechanics, real LLM in a kitchen, real LLM in a
multi-room apartment.

**F13. Scale does not buy prospective memory** (fig_model_scale.png; Sonnet
n=8 vs Haiku n=20). Sonnet's no-store arm (37.5%) exactly equals its
no-intention control: the stronger model's apparent memory is 100% common
sense. Commission softens (60→37.5%) but persists; the naive LLM coroutine
still fails (12.5%); the typed scheduled store still wins (87.5%, violations
0%). The ranking is scale-invariant — memory architecture, not model size, is
the decisive variable.

**F14. Perception costs ~30 points but preserves the mechanism ranking**
(night5.csv, RGB tier). Replacing the privileged text observation with raw
320px frames: sched 95→62.5, bank 95→62.5, commission still 75%, common-sense
floor still present (control 25%). Privileged-tier conclusions transfer to the
VLM tier shifted downward.

**F15. Multi-intention load breaks naive scheduling** (fig_load_llm.png).
The typed+scheduled store that dominates at one intention collapses under
load (90/30/20% for 1/2/3 intentions) and is beaten by always-inject at load
3 (60%). Uniform resurfacing of all intentions is not a schedule. Which
intention to resurface, when, under load — that is the open problem this
benchmark now poses cleanly.

**F16. Commission is a schedule property, not a load property**
(sched_geometry.csv, mock actor, n=24/cell, fig_sched_geometry.png). With a
rule actor that has no attention limits, executed-after-cancel is fully
determined by the injection schedule and indifferent to load: bank/rr/sight
leak 75% (early cancel) / 42% (late) at loads 1, 2, and 3 alike; a mechanical
strikethrough (rrn: strike note on cancellation + one-time notice) is 0% at
every load, at under half of bank's injection cost. The cancellation message
falls out of the window while the original note keeps arriving — commission is
window eviction plus schedule persistence, reproducible without any model.

**F17. The mechanical load loss is visibility, not interference; the LLM's
collapse is attention tax, now quantified.** Full injection loses 0.88 → 0.83
→ 0.69 EXEC across loads 1-3 on the mock — and every lost episode traces to a
trigger that never entered the field of view on the fixed chore route (seeds
17/20/23 fail under every policy at load 1). The information floor at load 3
is 0.69; the real Haiku sched agent sits at 0.20-0.30 — an attention tax of
40-50 points that no injection schedule can explain. EXEC should therefore be
reported conditioned on trigger visibility (never-visible episodes belong to
the NOTICE stratum).

**F18. Sight-triggered injection is mechanically optimal and behaviorally
broken.** On the mock, injecting a note only when its trigger is visible
matches bank's EXEC at every load for one fifth of the cost (22.8 vs 120
notes/ep at load 3) — mechanically it is the frontier. Real LLMs collapse on
exactly this policy (F5/F11): retrieval at cue onset arrives too late without
prior activation. The gap between the mechanical frontier and LLM behavior is
a clean measurement of the prior-activation requirement (Gollwitzer's
implementation-intention effect, machine edition).

*Replication note: the full grid was re-run at n=48/cell
(sched_geometry_n48.csv, 2160 episodes): every number above moves by at most 5
points and no ordering changes (bank EAC 77/48%, rrn 0 everywhere, information
floor at load 3 = 0.74, every5 starvation intact). A same-seed double-run
determinism probe produced bit-identical event-log hashes.*

**F19. The three-way trade-off exists already at the information layer.**
Sparse injection (every 5th step) starves execution mechanically (-30 pts) but
also leaks fewer commissions than bank (58% vs 75% early-cancel): fewer
post-cancel reminders, fewer violations. Cost, execution, and compliance pull
in three directions before any model enters the room; LLM attention then
shifts every curve down by its own tax. Scheduling theory has a mechanical
floor to build on.

## Solidification night 08-23 (zero API; suite frozen; all n≥48)

**F20. The triptych, now on the frozen benchmark at n=50** (suite_thor_v01.csv,
fig_suite_headline). Dev headline, memory contribution net of a clean control
(MEM): no store 0%; naive store 88% EXEC but **78%/46% executed-after-cancel**
(early/late); typed store + mechanical 6-step scheduler 58% EXEC with **0%**
violations on both arms. The scheduler's 30-point EXEC cost is the beat-gap
(triggers sighted between resurfacings), the mechanical face of "uniform
resurfacing is not a schedule" (F15) — visible already at load 1.

**F21. Everything transfers to unseen scenes.** THOR test split (FloorPlan2/3/4,
seeds 100+): scripted ladder unchanged (95.8%), bank 68.1% EXEC / 38.9% EAC,
sched 48.6% / 0%. Habitat castle: patroller collapses 75.5→29.2% (the F9 scale
law, reproduced on frozen episodes) while oracle stays 100%; bank 45.8/41.7,
sched 25.0/0. Rankings invariant; absolute EXEC scene-dependent as designed.

**F22. Cancel-retention half-life, finalized cross-engine**
(fig_window_parity). THOR-mock bank EAC falls 71→70→61→47→18% for
w=2→16; Habitat mock-bank 70→68→65→64→55%. The strikethrough controls
(rrn / habitat sched+rwim) sit at exactly 0% at every window in both engines.
Commission is window eviction plus schedule persistence in any engine; only
explicit revocation bookkeeping eliminates it at every window size.

**F23. Three graders, same episodes: only world-state sees the record**
(grading_records_0823b, n=1440 cancelled intentions, 654 world violations,
probes given the actor's exact final-step information). A selection-style
"would you act on it now?" probe at episode end **passes 52.9% of violators**
(their disposition is clean by then; the violation lives in the history). A
QA-style "was it cancelled?" quiz passes no violators but **false-alarms on
63.4% of clean episodes** (starved schedules leave no recitable cancellation
even when no violation occurred). World-state adjudication is the only regime
that grades the record rather than the disposition — the survey's structural
claim, now with numbers.

**F24. The validity probes caught three real bugs before any LLM token.**
(a) Control-twin contamination: bank/rwim/sched injected "you promised X"
into episodes where nothing was ever briefed — memory policies fabricating
intentions; caught by control EXEC ≈ live EXEC, fixed by `has_intention`
gating in both engines. (b) A silent policy gap: mock "sched" wasn't
implemented and degraded to "none" (EXEC 0). (c) A same-step tie: THOR's
late cancel (delay+2) coincides with the fastest scripted response, making
strict-EAC definitionally 0 on that one arm for step-8 agents (deaf: 47/50
loose vs 0 strict); Habitat's +4 geometry is unaffected; v0.2 will enforce a
≥1-step gap. Deaf calibration is exact on early arms in both engines.

*Suite status: epm_v0.1 frozen (6000 THOR + 1564 Habitat episodes, 1891
matched twin groups, SHA256 manifest); oracle audits green; determinism
bit-identical; checkers.py ships with 8 synthetic-log unit tests. LLM grid is
one command (`llm_grid_0823.sh`), priced at ~$128 (`estimate_llm_cost.py`);
blocked only on a key: the stored key now returns 401 invalid — replace, not
recharge.*

## LLM-tier protocol v2 (2026-09-12) — OpenRouter + interface fixes

OpenRouter routing added (`agents._client/_call`: model ids with a vendor
prefix go to the OpenAI-compatible endpoint; Anthropic path unchanged).
First cheap-model pilot (gpt-4o-mini) exposed an *interface* defect that
would have unfairly tanked small models: the model wrote `put Lettuce` (the
held object) where the env expects `put Fridge` (the receptacle), failed 17
times in a row, and never learned it — action results were not fed back.
Fixes: (1) ACTOR_SYSTEM now documents each verb, `put T` = receptacle;
(2) each observation is prefixed with `Last action: ... -> OK/FAILED (why)`;
(3) parser accepts "X into Y", strips articles, canonicalises object names
case-insensitively against the scene. Effect on gpt-4o-mini, live arm: chores
0/0 -> 6/4, EXEC reproduced at step 7. Consequence: the August Haiku pilot
(old protocol) is NOT comparable and is superseded by the v2 grid. Mock and
scripted tiers untouched (`env.observe()` unchanged). Measured cost ~45k
tokens/episode; per-episode price list in `估价` below.

**F25 (2026-09-12, gpt-4o-mini, n=10/arm, protocol v2).** Headline cell:
no store 10% EXEC (control 0%); naive store 100% EXEC, **80%/30% EAC**;
typed+scheduled store 90% EXEC but **90%/30% EAC** — the scheduler did NOT
zero commission for this small model, unlike the mock (0%) and the August
Haiku pilot (10%). Traces explain it: the v1 revocation note read
"[status: CANCELLED, do NOT do it] If you ever SEE the CoffeeMachine ON, turn
it off." The model turned it off at t=7 citing "as per my instructions" — it
latched onto the restated imperative and ignored the status tag. The mock's
strikethrough notice never restates the imperative, so the two tiers' sched
arms were not semantically matched. Fix: `sched` v2 note carries only the
revocation ("...was cancelled by the user. Do NOT touch the X, even if you
see it ON."); v1 wording kept as `sched1` for an ablation. Hypothesis to
test: **restating the imperative inside a revocation note re-primes
execution in small models** (a machine analogue of ironic-process /
prior-activation effects). Cost so far: $0.62 for 120 episodes.

**F26 (2026-09-12, gpt-4o-mini, n=10/arm). Revocation wording alone flips
commission from 90% to 0%.** Same model, same 6-step schedule, same
episodes; only the cancellation note changed. v1 note (status tag + restated
imperative): EXEC 90%, EAC 90%/30%. v2 note (revocation only: "...was
cancelled by the user. Do NOT touch the X, even if you see it ON."): EXEC
90%, **EAC 0%/0%**, at ~19k tokens/episode vs 45k for the naive store. This
is the LLM-tier twin of the mock result (strikethrough zeroes commission) and
adds a prompt-level mechanism: a restated imperative inside a revocation
re-primes execution in a small model. Pilot-scale; to be confirmed at n=50
and across families (DeepSeek/Llama/Qwen running).

**Protocol v3 (2026-09-12 evening).** DeepSeek-V3 under v2 averaged 8.7
steps and 0.5 chores per episode: it searched cabinets for the lettuce
instead of `goto Lettuce` (did not know goto works on unseen objects) and
declared `done` early — an interface-literacy confound that would turn the
EAC comparison into a who-quits-first contest. ACTOR_SYSTEM v3 states (a)
goto works for any object type even if not visible, (b) done only after
every listed chore is complete. All v2 LLM runs (gpt-4o-mini 150 eps,
partial DeepSeek/Llama) archived under results/protocol_v2/ and superseded;
F25/F26 remain valid as within-model comparisons but are re-run under v3.

## Novelty radar 2026-09-10 (claim re-verified)

Question: is EPM-Bench the first embodied prospective-memory benchmark?
Swept (abstract/task-list level): RoboMemArena 2605.10921 (26 manipulation
tasks: transfer/occlusion/counting/sequence — all retrospective, no cancel),
RoboMME-Interference 2606.22338 (cross-session recall under distractors),
RMBench 2603.01229 (memory-dependent manipulation, retrospective), PRISM
2605.11534 ("intent" = inferring user intent, not deferred intentions),
WatchAct 2606.26443 (reasoning about completed human actions), LongAct
2605.14504 (free-form long-horizon chores), NCP-Bench 2608.08160 (text-only
narrative commitments), PIS 2609.01272 (typed intention store, text PM-Bench
only, no cancellation). None contains an instruction-level deferred intention
with a cancellation condition graded from world state.

**The one real neighbour: Chameleon 2603.24576 (v2, June 2026)** keeps the
title "Control-Indexed Prospective Memory" and ships Camo-Dataset, a
real-robot benchmark it calls PM. Full-text read (2026-09-10): its three tasks
(clean a specified plate / shell game / add seasonings) are delayed-response
tasks — retain *evidence* (which cup) until a fixed, annotated decision stage
t_d at a canonical pose. "Prospective" there means the working state is
trained (Control-JEPA) to predict future control context — a representation
property, not the PM memory system. No instruction is stored (task fixed;
hidden variable z varies), no cue must be noticed, no distractor task, no
revocation; MSR/DSR/SR scored by two human raters; 3 tasks x 36 rollouts.
Psychology mapping: retrospective content in a delayed-response paradigm;
"add seasonings" ≈ output monitoring, still no deferred intention. Consequence: the unqualified phrase "first
execution-graded PM benchmark in 3D worlds" is contestable and was REMOVED
from the paper. Claim now reads: first benchmark grading the *full lifecycle
of instruction-level deferred intentions, including cancellation*, from world
state in embodied environments. Related work sharpened accordingly;
RoboMemArena and RMBench added as retrospective neighbours.

## Design lessons (hard-won, validated by adversarial reference agents)

1. Cancellation compliance must count only executions strictly after delivery.
2. Cancellation timing must respect the fastest possible response.
3. Proximity is not execution: require arrive-and-declare (or a state toggle).
4. In-flight revocation must abort a response leg already underway.
5. Patrol intervals shorter than one patrol leg cause goal thrashing.
6. Single-room scenes saturate easy conditions; effects need hard delays or
   multi-room structure.
7. A rule-based window-bounded mock actor flushes out every information-boundary
   leak before any LLM spends a token.
8. Run overnight batteries under `caffeinate`; App Nap froze Unity for hours.

## What this sets up

The scripted ladder (negligent → opportunistic → idle → patrol → smart patrol →
informed → oracle) brackets the space an LLM agent must beat; the mock triptych
predicts exactly where frozen LLMs should fail (eviction, commission) and what
a RWIM-style coroutine should fix. The LLM batteries are wired and fail-fast
(`llm_pilot.sh`, THOR; habitat tier needs `anthropic` installed in the conda
env) — one command once API credits exist.

## 2026-09-13 night — the "bad news" was a measurement artefact, and a real confound (F27–F29)

**F27 — Retrieval-given-encounter is at ceiling under sched, on both models.**
Decomposing EXEC = NOTICE × P(exec | trigger seen) on the live arms (protocol v3):

| model | policy | n | NOTICE | exec\|seen | EXEC |
|---|---|---|---|---|---|
| gpt-4o-mini | none | 10 | 30% | 0% | 0% |
| gpt-4o-mini | bank | 10 | 70% | 71% | 50% |
| gpt-4o-mini | sched | 43 | 95% | **100%** (41/41) | 95% |
| DeepSeek-V3 | none | 10 | 20% | 0% | 0% |
| DeepSeek-V3 | bank | 10 | 90% | 89% | 80% |
| DeepSeek-V3 | sched | 10 | 30% | **100%** (3/3) | 30% |

DeepSeek's "30% EXEC under sched" is entirely a NOTICE failure: in all 7 misses
`first_visible_step` is empty — the trigger never entered its view before it said
done. The briefing wording is "If you ever *notice* the X is ON…", so encounter is
the cue condition by construction; exec|seen is the faithful memory metric and
NOTICE is the (separately reported) monitoring metric. Mirrors the focal/non-focal
cue effect in human PM.

**F28 — Exposure-conditioned EAC (fairness check).** Violation rate restricted to
episodes where the trigger was actually seen ON after the cancellation arrived
(from per-step logs; violation = eac_strict):

| model | policy | variant | n | exposed | viol | viol\|exposed |
|---|---|---|---|---|---|---|
| mini | bank | early / late | 50/50 | 36 / 28 | 34 / 22 | **94% / 79%** |
| mini | sched | early / late | 50/50 | 18 / 18 | 1 / 5 | **6% / 28%** |
| mini | sched1 | early / late | 10/10 | 3 / 2 | 3 / 2 | 100% / 100% |
| DeepSeek | bank | early / late | 15/15 | 12 / 10 | 12 / 8 | 100% / 80% |
| DeepSeek | sched | early / late | 28/21 | 5 / 0 | 0 / 0 | 0% / – |

The sched advantage survives conditioning, but exposure is lopsided (sched
episodes are short) and DeepSeek-sched has ~zero exposure, so its 0% is
uninformative. Field semantics learned: `executed_after_cancel` (non-strict)
includes the cancel_late tie (exec at t=7 < cs=8); use `eac_strict`.
`trigger_on` in dump logs is post-action state.

**F29 — Confound: sched carried the intention but not the chore list.** `bank`
re-injects the whole briefing (chores + instruction) every step; `sched` injected
one intention line every 6 steps. The chore list scrolled out of the 6-step
window, so sched agents did ~2 of 6 chores and said done (mini 2.6 vs 7.4 chores;
DeepSeek 2.1 vs 5.9) → short episodes → low exposure. Not a memory effect; an
information-asymmetry artefact.

**Protocol fix — `sched2` (information-matched sched).** Every step injects
`[TASK BOARD] <the briefing's chore sentence verbatim>` + the v2 status-tracked
intention line (active / CANCELLED-revocation-only). Differs from bank ONLY in
how the intention is represented. Smoke (mini, cancel_late, 2 eps): 40 steps,
9–11 puts, ~55k tok — episode length now matches bank. Running: sched2 on both
models, cancel arms n=50 first, then live/control. Old `sched` is kept as the
"intention-only, no task board" ablation; `sched1` as the wording ablation.

**F30 — The information-matched control confirms it: representation, not exposure
(mini, cancel arms, n=50 per cell, 2026-09-14 morning).**

| policy | chores | steps | tok/ep | EAC early | EAC late | pooled (95% Wilson) | viol\|exposed |
|---|---|---|---|---|---|---|---|
| bank (raw briefing every step) | 7.3 | 40 | 54k | 68% | 44% | 56% [46,65] | 94% / 79% |
| sched1 (status + restated imperative) | 2.0 | 20 | 19k | 62% | 22% | 42% [33,52] | 100% / 61% |
| sched (intention-only, no task board) | 2.6 | 21 | 19k | 2% | 10% | 6% [3,12] | 6% / 28% |
| **sched2 (task board + status-tracked intention)** | 8.1 | 40 | 56k | **8%** | **6%** | **7% [3,14]** | 14% / 14% |

sched2 matches bank on chores, episode length, tokens and exposure (28/21 exposed
vs bank's 36/28) and differs ONLY in how the intention is represented. Violations
56% → 7%, Fisher p = 3e-13. The F29 confound is closed.

Wording ablation replicated at n=50: sched1 (restated imperative after the
CANCELLED tag) 42% vs sched2 7%, p = 7e-9; sched1 vs bank p = 0.07 (not
distinguishable). A revocation note that repeats the instruction is, for this
model, about as bad as no revocation bookkeeping at all.

Headline for the paper: same model, same information, same exposure — status-
tracked bookkeeping cuts cancelled-intention execution from 56% to 7%.

**2026-09-14 night plan (three engines).** Engine 1–2: DeepSeek sched2 cancel
arms → live/control; then Tier A (Llama-3.3-70B, Gemini-2.5-Flash-Lite:
none/bank/sched2 × 4 variants, n=50, smoke-gated). Engine 3 (`run_sweep.py`, a
copy of run_suite.py so the 2-engine queues' pgrep does not count it): Tier C
robustness on mini, bank vs sched2, n=20 per cell — (a) delay sweep 3/10/14 on
dev (`llm_or_gpt4omini_delay.csv`), (b) held-out kitchens FloorPlan2/3/4 on the
test split (`llm_or_gpt4omini_test.csv`). Load sweep deliberately NOT queued:
`sched`/`sched2` read the single `spec["intention"]`, so load>1 (several
intentions) needs a multi-intention task board first — otherwise the comparison
would be unfair to sched2. Qwen3-32B dropped (returns empty content via
OpenRouter chat API); GPT-4o dropped (~$0.13/ep).

## 2026-09-15 early morning — six model families in, three new findings (F31–F33)

**F31 — Frontier models violate too (cancel arms, n=20 per variant, bank vs sched2).**
Claude Sonnet 5: bank 13/40 (33%) → sched2 0/40. GPT-5.5: bank 13/40 (33%) →
sched2 0/17 (run cut by credit exhaustion; 23 eps pending). The frontier violation
rate under a raw store is about half the cheap-model rate (33% vs 55–64%) but far
from zero; status-tracked bookkeeping takes both to 0. "A stronger model fixes
it" is now an empirical no.

Main table state (pooled cancel arms, n=100 unless noted):
| model | none | bank | sched2 |
|---|---|---|---|
| gpt-4o-mini | 0/20 | 56% | 7% |
| DeepSeek-V3 | 1% | 64% | 3% |
| Llama-3.3-70B | 50%* | 57% | **0%** |
| Gemini-2.5-Flash-Lite | 3% | 55% | 1% |
| Claude Sonnet 5 (n=40) | – | 33% | 0% |
| GPT-5.5 (n=40 / 17) | – | 33% | 0% |

**F32 — Held-out kitchens (mini, cancel_early, n=20 per scene).** FloorPlan2:
bank 8/20 vs sched2 0/20; FloorPlan3: 13/20 vs 0/20; FloorPlan4: 17/20 vs 7/20.
Live-arm EXEC matched across policies in every scene. FloorPlan4's triggers are
Faucet/Toaster; every sched2 violation there cites the appliance state ("The
Faucet is ON and I need to turn it off") with the CANCELLED note present —
prior-driven, not instruction-driven (see F33).

**F33 — The common-sense floor, measured by the control twins.** Control twins
(no instruction, no cancellation) show how often a model switches the trigger
off spontaneously: gpt-4o-mini 2–8%, DeepSeek 0–4%, Gemini 4–10%, **Llama-3.3-70B
58%** (29/50; reasons: "turn it off for safety and energy efficiency"). Llama's
50% EAC under `none` (*) is therefore not memory at all — it is the prior; the
twin design is what lets us say so. Notably sched2's CANCELLED note suppresses
even Llama's prior (0/100). Violation by trigger type, all models pooled: bank
46–66% (Faucet highest, 66%), sched2 3–6% — the fix is uniform across trigger
types. Paper must report EAC alongside the control-twin floor (or as
EAC − floor); reviewers will otherwise read Llama's `none` row as a bug.

Ops: credit hit $0 at ~02:00 with 3180 episodes in. Remaining to plan: Llama
sched2/none live+control (188 eps, ~$1), GPT-5.5 sched2 (23 eps, ~$9), DeepSeek
bank live (9). `run_fill.sh` now waits for balance ≥ $8 and resumes everything.

**Protocol additions, 2026-09-15 evening.**
- `rwim3` = the self-bookkeeping memory agent (`rwim2`: a second LLM call per
  step that keeps a bank of intentions with status and emits a note only when a
  trigger looks satisfied or an intention was just cancelled) **plus the same
  `[TASK BOARD]` chore line sched2 injects**. Information-matched to sched2;
  differs in that the intention's status is inferred by the model from the
  conversation, not read from ground truth. Closes the "sched2 is an oracle"
  critique if it lands near sched2.
- RGB tier fix: in `--vision` mode the sliding-window history used to store the
  symbolic observation text (object list with ON/OFF states) — a leak of the
  symbolic tier into the pixel tier. History now stores only inventory /
  messages / injected note. `--size` flag added (300 px for vision; symbolic
  tier stays at 128 px, which never reached the model).

## 2026-09-15 morning — night 2 results (F34–F35), 3724 episodes total

**F34 — Self-bookkeeping (rwim3, gpt-4o-mini as its own memory manager,
n=20/variant).** Cancel arms: 5/40 violations (12%) — near sched2's 7%, far
from bank's 56%. But live arm EXEC 2/20 (10%) vs sched2 35/50 (70%); NOTICE is
fine (14/20) — exec|seen collapses to 2/14. MEM = +5 vs sched2's +66. The
memory agent's notes show why: it files *chores* as intentions ("if Microwave
is ON then put Potato into Microwave"), fires on the wrong conditions ("Bread is
in Fridge appears satisfied"), and is silent when the real trigger is ON. So a
small model's self-kept ledger is *compliant but forgetful*: it avoids acting on
cancelled intentions largely by failing to act on live ones. The sched2–rwim3
gap is the bookkeeping-quality gap — the concrete research target the benchmark
exposes. (Paper: report rwim3 as the non-privileged baseline next to sched2 as
the oracle-bookkeeping ceiling; never present sched2 as a method.)

**F35 — RGB tier is a perception floor for gpt-4o-mini (320×240, n=20).**
bank-rgb: EXEC 0/20, exec|seen 0/8; sched2-rgb: EXEC 5/20, exec|seen 5/9;
violations 0/20 in both (nothing executes, so nothing can violate). Traces at
the step where the lit trigger is in view: the model never mentions the
appliance state — s16 literally "put the Mug into the CoffeeMachine" while the
machine is ON. The ON state is not legible to this model at this resolution, so
the symbolic tier's memory effects cannot be replicated here by construction.
Note the sched2 note ("If you ever SEE the CoffeeMachine ON…") lifts exec|seen
from 0/8 to 5/9 — the memory representation primes perception. Running the same
RGB cell on Gemini-2.5-Flash-Lite (real vision, cheap) to see whether a
vision-capable model recovers the symbolic-tier pattern.

Addendum to F33 (Llama): sched2 raises Llama's EXEC by 0 points over its 54%
prior (MEM = +0), yet the CANCELLED note suppresses that prior completely
(0/100). Execution is prior-driven; revocation is instruction-driven.

Ops: GPT-5.5 sched2 fill (23 eps) launched separately — `run_fill.sh` never
included the frontier models. Balance $17.5.

**F36 (2026-09-15 afternoon) — frontier complete; RGB floor is general.**
GPT-5.5 sched2 cancel arms: 0/40 (bank 13/40). Both frontier families: bank
33% → sched2 0%. Gemini-2.5-Flash-Lite on the RGB tier (320×240, n=20):
bank-rgb exec|seen 0/15, sched2-rgb 1/17, chores 1.9–2.3, violations 0 (nothing
executes). Same perception floor as gpt-4o-mini. Conclusion for the paper: at
this resolution the cheap VLMs cannot read appliance state from pixels, so the
RGB tier cannot discriminate memory policies; report it as a negative result and
a limitation (the benchmark's symbolic tier isolates memory from perception by
design; the pixel tier awaits VLMs that can perceive appliance state). Frontier
VLMs on pixels were not run (Sonnet 5 ≈ $0.5/ep).

Night 3 plan (balance $7.4): Gemini replication of sched1 wording ablation
(cancel n=20), rwim3 (cancel + live/control n=20), delay sweep 3/10/14, held-out
kitchens — ~600 eps, ~$4.3. Makes the robustness section two-model.

**F37 (2026-09-16) — Gemini-2.5-Flash-Lite replicates every mini-only result.**
Night 3, ~600 eps, $3.5. All cells n=20 unless noted.
- Wording ablation: sched1 6/40 (15%) vs sched2 1/100 (1%) vs bank 55/100.
  Direction replicates; magnitude is model-dependent (mini sched1 = 42%).
- Self-bookkeeping rwim3: cancel 5/40 (12%, identical to mini's 5/40); live
  EXEC 3/20, NOTICE 14/20, exec|seen 3/14. "Compliant but forgetful" is not a
  gpt-4o-mini quirk.
- Delay sweep, bank vs sched2 (cancel_early / live): d3 13/20 vs 0/20
  (15 vs 14); d10 9/20 vs 0/20 (10 vs 7); d14 8/20 vs 0/20 (9 vs 6).
- Held-out kitchens: FP2 10/20 vs 0/20; FP3 10/20 vs 1/20; FP4 13/20 vs 0/20.
  FloorPlan4's 7/20 sched2 slips on mini (F32, faucet prior) do not appear on
  Gemini → that was a model prior, not a scene property.

**Experiments closed.** LLM tier ≈ 4900 episodes across 6 model families;
findings F1–F37. Remaining balance $3.84. Next phase: writing (results section
rewrite, figures from CSV, appendix traces).

## 2026-09-16 — venue decision and the AAMAS polish list

Decision: skip ICLR 2027 (no abstract registration); target AAMAS 2027 (abstract
10/1, paper 10/8). Reason: as written this is a measurement paper whose
headline can be read as "obvious prompt fix"; the two missing pieces (real
memory-system baselines; whether a stronger bookkeeper fixes it) cannot be done
convincingly in 9 days. Draft v02 (simple, 6 pp, ICLR template) is at
`paper_v02/epm_bench_v02.pdf`; all numbers via `make_stats.py -> stats.json ->
make_numbers.py -> numbers.tex`; figures via `make_figs.py`.

**New regimes (agents.py):**
- `retr` — retrieval memory (MemGPT/Mem0-style archival recall): every raw
  user-side step record (briefing, observation + feedback + user messages,
  WITHOUT injected memory blocks) is an item; query = current observation +
  messages; lexical IDF-weighted top-3 injected as `[RETRIEVED MEMORY]`.
- `summ` — rolling summary: every `window`=6 steps the memory model rewrites a
  <=80-word summary of chores/progress + standing instructions with status;
  injected every step as `[MEMORY SUMMARY]`.
- `--mem-model` — memory agent (rwim*/summ) on a different model than the
  actor; policy name becomes `llm-<mem>@<model>`; resume keys and trace names
  carry the tag. Planned: `rwim3@claude-sonnet-5` with a GPT-4o-mini actor
  ("does a better bookkeeper fix it?").
First smoke (before the raw-transcript fix) snowballed: retrieval items
contained earlier injections. Fixed by keeping `raw_transcript`.

**F38 (2026-09-17) — Real memory-system baselines fail too (gpt-4o-mini, n=20/variant).**
Retrieval memory (IDF-weighted top-3 recall of raw step records, MemGPT/Mem0
style): cancelled-intention execution 18/40 (45%). Rolling summary (rewritten
every 6 steps): 13/40 (32%). Both sit between the raw store (56%) and the
status-tracked store (7%). Mechanisms from traces: retrieval is driven by the
current observation, so once the appliance is in view it recalls observations
that mention the appliance (and the briefing) rather than the one-line
cancellation; the summary lags the cancellation by up to one rewrite window and
sometimes drops the "(cancelled)" qualifier when it compresses. Closes the
"raw store is a strawman" critique: the two most common deployed memory
designs reproduce the failure. Gemini replication pending (credit exhausted).

**F39 (2026-09-20) — baselines replicate on Gemini; paired twin tests.**
Real memory-system baselines, cancelled-intention execution (n=40 each):
gpt-4o-mini retr 45%, summ 32%; Gemini-2.5-Flash-Lite retr 38%, summ 15%
(bank 56% / 55%, sched2 7% / 1%). Same ordering on both models:
raw > retrieval > rolling summary > status-tracked.

Paired analysis on twin episodes (same seed, same variant; bank vs sched2; exact
McNemar): in all six models there is NOT ONE pair in which only sched2 violates.
Discordant pairs (bank only / sched2 only): mini 49/0, DeepSeek 61/0, Llama
57/0, Gemini 54/0 (n=100 pairs each), Sonnet 5 13/0, GPT-5.5 13/0 (n=40).
p from 4e-15 to 2e-4. This uses the twin design the way it was meant to be used
and should replace the pooled Fisher test as the headline statistic.

**Load sweep started.** sched2 now writes one status-tracked entry per
intention (identical output for load 1). In the suite's cancel variants with
load 2–3 only the FIRST intention is cancelled and the others stay live, so one
episode measures both EAC on the cancelled intention and execution of the
still-live ones (selective revocation). Running Gemini, loads 2 and 3, bank vs
sched2, cancel_early + live, n=20 → `results/llm_or_gemini_load.csv`.
`bash run_queue_load.sh openai/gpt-4o-mini gpt4omini` repeats it on mini after a
top-up. Still gated on credit: rwim3 with a Sonnet-5 bookkeeper (needs ≥ $12).

**F40 (2026-09-20) — load sweep, Gemini (n=20 per cell).** Two and three
concurrent intentions; in cancel twins only the first is cancelled.
| load | regime | cancelled one still executed | still-live ones executed (cancel twin) | live twin, mean executed |
|---|---|---|---|---|
| 1 | bank / sched2 | 60% / 5% | – | 60% / 50% |
| 2 | bank / sched2 | 70% / 10% | 55% / 40% | 52% / 42% |
| 3 | bank / sched2 | 60% / 10% | 35% / 40% | 43% / 30% |
The revocation fix holds under load and is selective (live intentions are still
served at a comparable rate). Execution of live intentions falls with load for
both regimes (the classic PM load effect). On Gemini sched2 executes live
intentions somewhat less than bank; on gpt-4o-mini it was the other way round.

**F41 — retr2 smoke (tombstone delivered by retrieval).** One Gemini episode:
the CANCELLED ledger entry was retrieved on 0 of 34 steps, including the step
where the trigger was ON and in view, and the agent violated. A status-tracked
entry does nothing if delivery is left to similarity retrieval, which is what
2609.08258 reports for deployed memory systems. Caveat: our retriever is lexical
(IDF overlap); an embedding retriever should be run as a robustness check
(sentence-transformers is not installed locally).

**VALIDITY ISSUE FOUND AND FIXED — control twins were not exposure-matched.**
Since the `has_intention` guard (2026-09-07) the control twin injected NOTHING
for every regime, so control episodes lost their task board and ended early:
bank/sched2 control vs live steps = 26 vs 40 (mini), 11 vs 38 (DeepSeek), 27 vs
40 (Llama), 18 vs 40 (Gemini). The control floor and MEM = live − control are
therefore biased (floor too low). EAC comparisons between regimes are NOT
affected (cancel twins were always full length). Fix: in control twins every
regime now injects its non-intention content (bank: the chores-only briefing;
sched2: the task board; retr/summ/rwim3 run normally); only the intention-only
regimes inject nothing. Smoke: control now runs 40 steps with 8–9 chores.
Exposure-matched control cells go to `results/llm_or_<tag>_ctrl2.csv`; the old
control rows must not be used for the floor.

Queued behind credit (`run_queue_after_topup.sh`, starts at balance ≥ $10):
(1) control rerun, 4 models, ~$5; (2) load sweep on mini, ~$2; (3) retr2 on mini
and Gemini, ~$2; then at ≥ $45: (4) Sonnet 5 and GPT-5.5 live + control, ~$46.
Separately `run_queue_bookkeeper.sh` (Sonnet 5 as memory agent) at ≥ $12, ~$6.

**Habitat LLM tier revived (2026-09-20 evening).** `pm_habitat.py` already had
a decision-level LLM actor (continue / respond / abort; chores are
auto-navigated; task = "if you ever see the red beacon, go to it and press
it", user may cancel). August pilot with Haiku, n=10 per cell
(`results/hab_real.csv`): none EXEC 0/10, EAC 0/10; bank EXEC 6/10, EAC 6/10;
sched EXEC 6/10, EAC 0/10 — the same pattern as THOR. Now: actor routed through
`agents._client/_call` (OpenRouter), regimes `sched2` (status-tracked entry
rewritten on cancellation) and `sched1` (status tag + restated imperative) added
with the THOR wordings, both injected every step for parity with `bank`; new
runner `run_suite_habitat.py` executes the FROZEN Habitat suite with resume and
per-step traces. Env: `~/miniforge3-x86/envs/habitat/bin/python` (openai
installed there today). Smoke (Gemini, cancel_early, seed 0): bank executes at
step 16 after a cancel at step 6 (violation); sched2 aborts. ~16k tok/ep
(~$0.002), ~35 s/ep. Running: dev/apartment_1, delay 10, seeds 0:50, four twins,
regimes bank/sched2 (`hab_or_<tag>.csv`) and none/sched1 (`hab_or_<tag>_abl.csv`);
Gemini now, gpt-4o-mini after the THOR core queue. Control twins are
exposure-matched by construction here (chores are automatic).

**F42 (2026-09-20 night) — the exposure-matched control twins change the Llama story.**
New floor (control twin now carries the task board, 40 steps) vs old:
gpt-4o-mini bank 8%→12%, sched2 4%→12%; Gemini bank 6%→12%, sched2 10%→10%;
DeepSeek bank 6%→10% (39/50 so far); **Llama bank 58%→8%, sched2 54%→13% (15 so far)**.
For three models the floor rises slightly, as expected. For Llama it collapses:
the old 58% was not a "common-sense prior" but IDLE behaviour. Without a task
board Llama ran out of chores it could remember and started switching
appliances off "for safety and energy efficiency"; with chores to do it almost
never does. Consequences:
- F33 must be rewritten. Llama is NOT an exception: its bank EAC of 57% is far
  above an 8% floor, i.e. memory-driven like the other models, and its live
  execution is memory-driven too (33/50 vs floor 4/50).
- The `none` regime has no task board in ANY twin, so Llama-none still idles:
  its 50% EAC vs ~50% none-control floor remains "not memory". The twin design
  still does its job, but the lesson is different: an idle agent's behaviour is
  a confound that only an exposure-matched control removes.
- The sentence "the CANCELLED entry suppresses even the habit" is no longer
  supported and must go.
The main claim (bank vs sched2 on cancel twins) is unchanged.

**F43 — Habitat v1 action menu leaked the intention (caught by the control twin).**
First Habitat run (Gemini, v1 prompt): bank EAC 48/70, EXEC 25/35, CONTROL
25/35; none EAC 46/68, EXEC 24/34, control 25/35. The agent pressed the beacon
in 71% of control twins, with or without memory, because the action menu
itself said `"respond": go to the red beacon now and press it`. (Haiku in the
August pilot was disciplined: none 0/10.) Run stopped after ~$0.6; results
archived in `results/habitat_v1_menu_leak/` as a methodological datapoint
(menus that name the target behaviour inflate the floor — the same reason
menu-based grading fails). v2 prompt describes the action space neutrally
(`continue / interrupt / resume`; "things you see are not tasks by themselves").
Smoke of control/live/cancel twins under v2 is running; relaunch only if the
control floor is low.

**Sonnet-5 bookkeeper, interim.** Policy name is `llm-rwim3@claude-sonnet-`
(truncated at 14 chars). Cancel arms complete: EAC 4/40 (10%; mini as its own
bookkeeper 5/40). Live arm so far: EXEC 1/9, exec|seen 1/5. A frontier memory
agent does not rescue execution so far.

**Habitat v2 prompt, smoke (Gemini, seeds 0–5, n=6 per cell).** Control: pressed
the beacon 0/6 under both regimes (5 of 6 saw it) — floor gone. Live: bank 5/6,
sched2 6/6. Early cancel: bank violated 5/6, sched2 0/6. Same pattern as THOR
with a clean floor. Full run relaunched (Gemini now, gpt-4o-mini after the THOR
core queue): `results/hab_or_<tag>.csv` (bank, sched2) and
`results/hab_or_<tag>_abl.csv` (none, sched1).

**BUG FOUND — F34 and the bookkeeper results are INVALID (2026-09-20 night).**
The memory agent of rwim/rwim2/rwim3 received trajectory entries cut at 200
characters. In the dev cell the deferred instruction sits at characters
~225–295 of the briefing (20/20 seeds start after 200), so the memory agent
NEVER SAW the instruction; it only learned that a coffee machine mattered from
the cancellation message. Found while asking why a Sonnet-5 bookkeeper had an
EMPTY bank for the whole episode and stayed silent on 15/15 episodes where the
trigger was lit and in view. Invalid: F34 ("compliant but forgetful", mini),
the Gemini rwim3 replication in F37, and the Sonnet-5 bookkeeper run (EAC 4/40,
EXEC 3/20). The memory agent also ran one step behind (it never saw the current
observation). NOT affected: none/bank/sched/sched1/sched2 (no truncation
anywhere on their path); retr and summ (cut at 300 chars; the instruction ends
before char 300 in 20/20 seeds, verified).
Fix = new regime `rwim4`: entries shown up to 800 chars plus the current
observation; same prompt and task board as rwim3. Smoke (Gemini): the memory
agent now emits "[MEMORY NOTE] The CoffeeMachine is ON, so I should turn it off"
at steps 6–8 and the actor executes. Running rwim4 for Gemini and mini (4 twins,
n=20); the Sonnet-5 bookkeeper rerun waits for balance ≥ $12 (~$7).
Lesson: every regime needs a per-episode sanity probe that the instruction is
present in what its memory component is shown at step 0.

**Bookkeeper comparison recorded before the bug was found (do not use):**
mini own ledger EAC 5/40, EXEC 2/20; Sonnet-5 ledger EAC 4/40, EXEC 3/20;
oracle sched2 (seeds 0–19) EAC 2/40, EXEC 16/20.

**F44 (2026-09-20 night) — Habitat replicates THOR, with a clean floor.**
Second interface bug found and fixed first: the observation always read "You
are doing chores", even while the robot was walking to the beacon, so after a
late cancellation the agent answered "continue" (meaning: keep doing chores)
and the controller kept walking it to the beacon. Rows produced under that bug
are archived in `results/habitat_v2_enroute_bug/`; control and cancel_early
were unaffected and were kept. After the fix (observation now says "you are on
your way to the red beacon", and "continue" means "keep doing what you are
doing now"), Gemini-2.5-Flash-Lite, n=49 per cell:

| regime | control | live EXEC | early-cancel EAC | late-cancel EAC |
|---|---|---|---|---|
| no store | 0/49 | 0/49 | 0/49 | 0/49 |
| raw store | 0/49 | 36/49 | **36/49** | **34/49** |
| status + restated imperative (sched1) | 0/49 | 44/49 | **0/49** | **0/49** |
| status-tracked (sched2) | 0/49 | 45/49 | **0/49** | **0/49** |

Same pattern as THOR and a cleaner floor (0/49 in every control cell). Two
differences worth noting: the raw store violates as often on late as on early
cancellation here, and the wording ablation does NOT reproduce (sched1 is as
good as sched2). Both plausibly because the Habitat task is a single
decision per step over a visible beacon with no object manipulation, so the
imperative has less to compete with. Report it as a boundary of the wording
effect, not as a contradiction. Remaining: gpt-4o-mini on Habitat (~$2, queued
behind balance ≥ $3).

**F45. The self-kept ledger, delivered in the fixed wording (`rwim5`), recovers
execution — and invents obligations.** Same bookkeeper as `rwim4` (gpt-4o-mini,
no ground truth), same ledger; the only change is that the injection is
RENDERED from the ledger in sched2's exact wording instead of a free-form
`[MEMORY NOTE]`. n=20 per cell, dev/delay 6/load 1, gpt-4o-mini actor:

| regime | who sets status | EXEC(live) | exec\|seen | EAC (pooled cancel) |
|---|---|---|---|---|
| bank | — | 28/50 56% | 80% | 56/100 56% |
| sched2 | harness (true) | 35/50 70% | 95% | 7/100 7% |
| rwim4 (free-form note) | mini | 5/20 25% | 36% | 6/40 15% |
| **rwim5 (fixed wording)** | mini | **12/20 60%** | **86%** | **3/40 8%** |

So the "compliant but forgetful" failure of F34/rwim4 was a DELIVERY-FORMAT
failure, not a bookkeeping failure: the same ledger, rendered as the
status-tracked entry, restores execution to the bank level while keeping
violations at the sched2 level. sched2 stops being an unreachable upper bound
and becomes a reachable target.

Trace audit (40 cancelled episodes): the bookkeeper wrote the CANCELLED entry
in 40/40, and once written it persisted to the end of the episode in 39/40
(the exception drops it at t=38-39 by marking it `done`). Revocation
bookkeeping is learnable.

BUT the ledger fabricates standing intentions it was never given, from the
chore list: in 36/60 episodes (60%) it contains at least one entry for a
non-trigger object ("If you ever SEE the Fridge ON, turn it off"; top
fabricated objects Fridge 9, Microwave 8, CoffeeMachine 8, Potato 7). The
actor acted on a fabricated entry — toggling off an object that was never
the subject of any instruction — in 12/60 episodes (20%). Live execution is
not hurt (8/11 with fabrication vs 6/9 without).

Reading for the paper: moving bookkeeping from the harness to the model does
not remove commission errors, it MOVES them. Harness bookkeeping: 7%
commission on cancelled intentions, 0 fabricated. Model bookkeeping: 8% on
cancelled intentions, plus 20% commission on intentions that were never
given. The benchmark's world-state grader sees both; a grader that only
scores the named intention would see only the first. Sonnet-5 as bookkeeper
is running to test whether fabrication is a small-model artefact.

**F45 addendum (Sonnet-5 bookkeeper, final n=20/arm, 2026-09-23 18:27).**
rwim5 with `--mem-model anthropic/claude-sonnet-5`, actor gpt-4o-mini:
EXEC 12/20 (60%), exec|seen 12/13 (92%), EAC 6/40 (15%; early 4, late 2).
Paired: vs sched2 EAC 2 vs 6 discordant p=0.29 (n.s.), EXEC 4 vs 0 p=0.12
(n.s.); vs bank EAC 17 vs 0 p=1.5e-5; vs rwim4 EXEC 0 vs 7 p=0.016.
Trace audit: fabricated intentions 0/60 (mini bookkeeper: 36/60); cancelled
entry held to the end 39/40 (same as mini); all 6 violations occurred with a
correct CANCELLED entry in front of the actor (same as mini's 3/3 and as
sched2's residual). Three variables separated: delivery FORMAT → execution;
bookkeeper CAPABILITY → fabrication; actor → the 7–15% residual, invariant
to who keeps the ledger. Paper §5.3 rewritten accordingly.

**F46 (2026-09-30) — the 14-object observation cap can hide a visible trigger.**
`observe()` lists at most 14 visible objects, alphabetically. Replaying 26
gpt-4o-mini cancel-early episodes (bank + sched2, seeds 0-19) at the step the
grader credits as first-visible: in 4/26 the trigger was visible per THOR but
absent from the text (16-26 visible objects; CoffeeMachine/Microwave). NOTICE
and exec|seen therefore overstate "seen" in ~10-15% of episodes; EAC and EXEC
are unaffected (they do not depend on NOTICE), and both designs are affected
equally. Paper §3.4 now states NOTICE is simulator-side and exec|seen is a
lower bound. env.py changed for v0.2: toggleables sorted first. Existing v0.1
results are NOT rerun. Script: audit_notice_cap.py, data: results/audit_notice_cap.json.

**F47 (2026-10-01) — load curve: the rewrite stops working at four intentions.**
gpt-4o-mini, delay 6, seeds 0-19, cancel-early EAC (n=20/cell):
bank 65/55/50/45%, retr 60/80/45/45%, retr2 55/55/60/58%, sched2 5/5/20/40%
for loads 1/2/3/4. At load 4 sched2 vs bank paired: 8 vs 6 discordant, p=0.79.
Mean fraction of live intentions executed (live arm): bank 50/48/35/35%,
sched2 80/62/45/49%. The sched2 entry is harness-written and correct in every
episode; the load-4 violations are the actor acting on an entry marked
CANCELLED among three active ones. Load 4 is the cap (four toggleable types in
FloorPlan1). New suite file suite/epm_v0.1_thor_load4.jsonl (80 episodes).
Paper: Table 3 (tab:load) in §5.4, "What remains open" paragraph in §6,
abstract/intro updated.

**F47 addendum (2026-10-01 evening) — loads 4-6 rerun under the v0.1 observation
ordering; the 40% cell is withdrawn.** The load-4 run above used observe() with
toggleables listed first (a 9/30 change made before that run), while loads 1-3
and the main table list objects alphabetically with the 14-object cap. Ordering
is now a flag (`ThorPMEnv(toggle_first=...)`, `run_suite.py --obs-v2`, default
old behaviour). Load 4 rerun and loads 5-6 added with LightSwitch and StoveKnob
as extra triggers (`suite/epm_v0.1_thor_load56.jsonl`, 80 episodes), all into
`results/llm_or_gpt4omini_load_v1obs.csv` (300 episodes, $3.5).
EAC cancel-early (n=20/cell), loads 4/5/6: bank 55/45/35%, retr2 65/35/45%,
sched2 30/30/35%. Paired bank vs sched2 discordant (bank-only/sched2-only):
7/2 p=0.18, 4/1 p=0.38, 3/3 p=1.0. Mean fraction of live intentions executed
(live arm): bank 30/21/17%, sched2 52/31/31%.
Reading: sched2's advantage shrinks from 50-60 points at loads 1-2 to zero at
load 6; bank's EAC falls because the actor does less of everything under load,
not because it honours the cancellation. Trigger-seen rates vary 10-17/20 per
cell (14-object cap); EAC among seen episodes is ~1/2 for sched2 and 1/2-2/3
for bank at loads 4-6, so the convergence is not a visibility artefact.
Full curve now: sched2 5/5/20/30/30/35%, bank 65/55/50/55/45/35%.
Paper: tab:load extended to six columns, §5.4 paragraph, §6 "What remains
open" and limitation ("capped at six"), intro answers paragraph + contribution
(2). Abstract sentence ("four ... 40%") still to be replaced by the user in
Overleaf. retr cancel-early at loads 4-6 (run_queue_load_retr.sh, 60 eps):
55/40/45%, so retr 60/80/45/55/40/45% over loads 1-6; table complete.

**F47 addendum 2 (2026-10-02) — overnight extension: seeds 20-39 for bank/sched2
at every load, summ and rwim5 at loads 2-6 (run_queue_load_night.sh, two parallel
queues, 780 eps, ~$10).** Merged numbers (loads 1..6; load 1 uses seeds 0-49 for
bank/sched2, others seeds 0-19/0-39 as noted; loads 4-6 from v1obs only):
EAC cancel-early: bank 66/55/60/60/42/45 (n=50,40..), sched2 8/10/22/22/32/38,
rwim5 15/10/25/30/25/40 (n=20), summ 35/35/60/50/40/50 (n=20),
retr 60/80/45/55/40/45, retr2 55/55/60/65/35/45.
Paired bank vs sched2 (bank-only/sched2-only): L1 29/0, L2 20/2, L3 16/1,
L4 18/3 p=0.001, L5 7/3 p=0.34, L6 7/4 p=0.55.
EXEC live (mean fraction executed): bank 62/50/37/33/22/20, sched2 70/65/56/57/31/32,
summ 85/68/43/28/24/18.
Reading (replaces addendum 1's "30-35% at 4-6"): the rewrite holds at 1-2, degrades
from 3, is still clearly better than bank at 4 (22 vs 60), and from 5 on is not
separable from bank (32/38 vs 42/45). The self-kept ledger tracks sched2. Paper:
tab:load replaced by fig_load (aamas2027/make_fig_load.py, figs/fig_load.pdf);
§5.4, abstract, intro (answers + contribution 2), §6 updated to "five or six,
about a third, not separable from the raw store".

**F48 (2026-10-02) — rescheduling: one message withdraws A and gives B.**
Variant `reschedule` (suite/epm_v0.1_thor_resched.jsonl, 40 seeds; run on 0-19):
load-1 cancel-early spec, intention A (event 6, cancel 3, `reschedule_to`=B),
intention B (another default trigger, event 11, `given_step`=3, NOT in the
briefing). Step-3 message: "About the <A>, never mind... Instead, if you ever
notice the <B> is ON, turn it off." Code: env.pending_messages combined message;
agents.py sched1e/sched2/retr2 skip entries before given_step. Grading reuses
EAC (acted on A after step 3) and executed (B done). mini, delay 6, n=20/design,
results/llm_or_gpt4omini_resched.csv ($1.6):
  bank   old 75%  new 10%   (briefing never contains B)
  summ   old 50%  new 50%
  sched2 old 20%  new 55%   vs bank: 11/0 p=0.001 (old), 0/9 p=0.004 (new)
  rwim5  old 20%  new 45%   vs sched2: 2/2, 2/0 (n.s.)
Reading: the rewrite handles an update, not only a deletion; the self-kept
bookkeeper reads both halves of one message. sched2's 20% on the old one is
above its 7% under plain cancellation (n=20, not separable) -- the message now
contains a fresh imperative. Paper: §5.4 "Rescheduling" paragraph; §3.5 counts.
Addendum (seeds 20-39 added, n=40): bank 68%/15%, summ 50%/58%, sched2 28%/50%
(vs bank 17/1 p=0.0001, 1/15 p=0.0005), rwim5 15%/48%. Paper updated to n=40.

**F49 (2026-10-02) — load curve on a second actor: the collapse is mini-specific.**
Gemini 2.5 Flash Lite, bank vs sched2, loads 1-6 (loads 1-3 from earlier files,
4-6 from results/llm_or_gemini_load_v1obs.csv, run_queue_gemini_load456.sh,
240 eps incl. live arms, ~$2.5), seeds 0-19:
EAC cancel-early: bank 60/70/60/55/40/45, sched2 5/10/10/5/5/5.
Paired bank-only/sched2-only: 11/0, 12/0, 10/0, 10/0, 7/0, 8/0 (p<=0.016 everywhere).
EXEC live frac: bank 60/52/43/34/24/19, sched2 50/42/30/26/18/11 (Gemini executes
less under sched2, as in the main table; the EAC gap is far larger than the EXEC gap,
so the low EAC is not inactivity).
Reading: on Gemini the rewrite holds through six intentions; the five-to-six
collapse (F47) is a property of GPT-4o-mini, i.e. a model x representation
interaction. Paper claims changed from "no design we tested does better at
five or six" to "depends on the actor: mini ~1/3 under every design, Gemini
<10%". Touched: abstract, intro answers + contribution 2, §5.4 load paragraph
+ fig_load (Gemini dashed in panel a), §6 what-remains-open, conclusion.

**F50 (2026-10-03) — table fill: floors.** (run_queue_table_fill.sh, run_queue_rwim5_ctrl.sh)
Control (exposure-matched, delay 6, load 1, seeds 0-19):
- GPT-5.5 bank 2/20 (10%), Claude Sonnet 5 bank 2/20 (10%) -> frontier EAC 32% is ~22 points above floor.
- GPT-4o-mini self-kept ledger (rwim5, mini bookkeeper) 9/20 (45%) vs 12% for sched2/bank: with NO
  instruction given the bookkeeper still writes a standing intention about the trigger and the actor
  acts on it. Independent confirmation of the fabrication finding (F45) from the control variant.
  Sonnet-bookkeeper control not run.
- retr/summ floors from existing ctrl2 data: mini retr 4/20 (20%), summ 5/20 (25%); Gemini retr 4/20
  (20%), summ 2/20 (10%). NOTE: summ EAC is only 7 and 5 points above its floor on these two models.
Paper: Table 2 floor column filled for these rows; one clause in §5.1 (frontier floor), one sentence
in §5.3 (ledger floor); "none at floor for five of six models" corrected to "three of the four it was
run on". DeepSeek/Llama RETR+SUMM still running; frontier live arms gated at balance >= $30.

**F51 (2026-10-03) — RETR and SUMM on DeepSeek and Llama (table fill).** seeds 0-19, delay 6, load 1.
EAC pooled (n=40) / EXEC (n=20) / exec|seen / floor (n=20):
  mini     retr 45% / 60% / 12/14 / 20%   summ 32% / 85% / 17/19 / 25%
  DeepSeek retr 62% / 80% / 16/17 / 10%   summ 32% / 70% / 14/15 / 15%
  Llama    retr 52% / 75% / 15/17 / 15%   summ 20% / 95% / 19/20 / 5%
  Gemini   retr 38% / 60% / 12/15 / 20%   summ 15% / 50% / 10/19 / 10%
Reading: retrieval is a violator on all four models (25-50 points above floor). The rolling summary is
intermediate (5-17 points above floor): a summary is itself a model-rewritten record, so it carries
the cancellation part of the time. The abstract's "briefing, retrieval, summary ... about half" was
too strong for the summary and has been reworded (bank 55-64 / 32 frontier; retrieval as bad;
summary 15-32). Table 2 now has all five designs for the four mid-sized models.
Cancel timing (not in the paper yet): bank early vs late = 68/44, 76/52, 70/44, 64/46 (mini,
DeepSeek, Llama, Gemini): the cancel message is still in the 6-step window in cancel-late.

**F52 (2026-10-05) — main table complete at 50 seeds; the self-kept ledger on all four mid-sized actors.**
(run_queue_seed50.sh, run_queue_rwim5_all.sh; audit_ledger_all.py -> results/audit_ledger_all.json)
RETR, SUMM, RWIM-LEDGER (rwim5, bookkeeper = the actor's own model) now have 100 cancelled / 50 live /
50 control episodes per model, like NONE, BANK, SCHED. Paper names: sched2 -> SCHED, sched1e -> SCHED-TAG,
retr2 -> RETR-SCHED (code and CSVs keep the old names).
EAC / EXEC / exec|seen / floor:
  mini     retr 44/54/27of32/14  summ 39/84/42of47/16  rwim5 7/70/35of39/44   sched 7/70/35of37/12
  DeepSeek retr 53/74/37of40/10  summ 36/74/37of40/12  rwim5 3/76/38of40/10   sched 3/78/39of42/12
  Llama    retr 51/66/33of41/14  summ 17/90/45of48/8   rwim5 1/60/30of33/8    sched 0/54/27of30/10
  Gemini   retr 31/52/26of36/14  summ 12/58/29of45/10  rwim5 0/52/26of40/26   sched 1/50/25of38/10
RWIM-LEDGER vs SCHED, EAC, paired: 8 vs 8 discordant in 400 (per model 4/4, 3/3, 1/0, 0/1).
RWIM-LEDGER vs BANK: 2 vs 223 in 400 (two reverse pairs exist: mini 1, DeepSeek 1).
All four bookkeepers marked the true entry cancelled in 400/400 cancelled episodes (399 kept it to the end).
Ledger audit (episodes with an entry the user never gave / actor tried to switch off such an object):
  instruction given (150 eps): mini 84 (56%) / 29 (19%); Gemini 81 (54%) / 3 (2%); DeepSeek 0 / 0; Llama 0 / 0;
  Sonnet-5 bookkeeper (60 eps) 0 / 0.   control (50 eps): mini 50 / 32; Gemini 50 / 11; DeepSeek 0; Llama 0.
  Nearly all fabricated entries are chore-derived (the bookkeeper files a chore as a standing instruction,
  against its prompt); the renderer shows every entry in the fixed "if you ever SEE X ON, turn it off"
  wording and does NOT render the ledger's instruction field, so a mis-filed chore reaches the actor as a
  switch-off instruction. This is stated in §5.3. Floors: mini 44%, Gemini 26% vs DeepSeek 10%, Llama 8%.
SUMM mechanism (mini, 39 violations): in 28 the summary at the violating step already read
  "... turn it off (cancelled)"; in 11 it still said active. The summarizer writes the annotate-style entry
  that the wording ablation shows does not work. RETR (mini, 44 violations): cancellation absent from the
  retrieved items in 36, original instruction retrieved in 31.
Six intentions, first cells (cancel-early, n=20; run_queue_load6_table.sh, suite epm_v0.1_thor_load6_full.jsonl):
  BANK vs SCHED EAC: mini 35/35 (3 vs 3), Llama 45/30 (3 vs 0, p=0.25), Gemini 45/5 (8 vs 0), DeepSeek 60/10 (10 vs 0).
  Two of four actors keep the rewrite's advantage at six, two lose most of it. Remaining cells still running.
Incident: two processes created the same new CSV (deepseek/llama load_v1obs) and the header landed on line 2;
  fixed by stopping, moving the header, restarting with one writer per file. All 31 result files audited.
Paper: Table 2 (six designs, RWIM-LEDGER before the reference row), fig_ablation and fig_ledger regenerated
(ledger figure now five bookkeepers), §5.1/§5.2/§5.3, §6, conclusion, abstract updated; body 8 pages.

**F53 (2026-10-05) — six intentions, full table (four variants, 20 seeds).** results/load6_table.json, results/load6_seen.json
Pooled EAC (n=40, early+late) / EXEC (mean share of six live intentions) / floor (first trigger off in control). Half-up rounding.
  GPT-4o-mini: NONE 5/3/10, BANK 25/17/5, RETR 33/13/15, SUMM 38/18/15, RWIM-LEDGER 33/30/50, SCHED 23/31/5. BANK vs SCHED 5 vs 4 (p=1).
  DeepSeek:    BANK 50/33/10, RWIM-LEDGER 10/28/10, SCHED 10/24/10. BANK vs SCHED 16 vs 0 (p=3e-5).
  Llama:       BANK 33/30/5,  RWIM-LEDGER 23/25/5,  SCHED 20/29/5.  BANK vs SCHED 5 vs 0 (p=0.06).
  Gemini-FL:   NONE 3/2/10, BANK 35/19/10, RETR 28/8/10, SUMM 13/9/10, RWIM-LEDGER 10/13/20, SCHED 5/11/10. BANK vs SCHED 12 vs 0 (p=0.0005).
Reading: the rewrite still works at six on DeepSeek and Gemini, is not significant on Llama, is gone on mini. No episode executes all six.
Decomposition of the low EXEC (live variant, 120 intentions per cell, per_intention in the dump JSONs):
  only 38-52% of triggers come into view after firing (SCHED: mini 52, DeepSeek 42, Llama 49, Gemini 38);
  exec|seen under SCHED: mini 60% (37/62), DeepSeek 57% (29/51), Llama 59% (35/59), Gemini 28% (13/46),
  against 95/93/90/66% at one intention. So about half of the shortfall is exposure, half is seen-but-not-acted.
Note: the figure (fig_load) is cancel-early only with n=40 for mini BANK/SCHED; the table pools early+late on seeds 0-19.

**F54 (2026-10-05) — simulator artefact: an open microwave cannot be switched on. Oracle is not 100%.**
Found while computing an oracle ceiling for load 6. `put Microwave` opens the door, the PutObject then fails in FloorPlan1
("No valid positions to place object found"), the door stays open, and the event engine's forced ToggleObjectOn fails
("Target must be closed to Toggle On!"). env.fired is still set, so the event counts as fired but the trigger never lights.
  Main cell (delay 6, load 1, seeds 0-49): trigger=Microwave and first chore=Microwave in seeds 17, 30, 33. Oracle EXEC = 47/50.
    For LLM actors it depends on timing (mini executed in 7 live episodes on those seeds), so the seeds are not strictly dead.
    Matched across designs, so comparisons stand; absolute EXEC/EAC are slightly deflated. Paper §3.5 now says 47 of 50.
  Load 6: Microwave is always one of the six triggers and 17/20 seeds have a Microwave chore; the door was opened before the
    Microwave event in 8-12 of 20 live episodes per cell (at most 1 of 6 intentions each, <=8% of intentions).
  Scripted oracle at load 6: 76% mean share (10/20 all six). Shortfall is artefact: the microwave case (6 seeds at 5/6) and a
    stall (4 seeds: toggle_off StoveKnob fails while the oracle still holds the object from the failed microwave put, loops).
    Not used in the paper as a ceiling for that reason.
  Also: the chore "put X into the Microwave" is infeasible in FloorPlan1 with this action set. Chores are not graded.
  Not fixed in code: changing the event engine would change every existing episode. Candidate for v0.2 (close the door before
  the forced toggle, or exclude the trigger type from chore receptacles).
Paper after F53/F54: Table 2 has "Six intentions" EAC/EXEC columns (exec|seen column dropped), Load paragraph rewritten for four
actors, abstract/intro/discussion/conclusion load claims updated, §3.5 suite count 320 and oracle sentence corrected, Pixels
paragraph folded into Limitations, several duplicated sentences cut; body exactly 8 pages. Backup before edits: scratchpad backup_1005b/.

**F55 (2026-10-06) — six intentions at 50 seeds, all four actors x six designs x four variants (4,800 episodes).**
results/load6_table_s50.json (aamas2027/make_table_load6.py), results/load6_seen_s50.json. Pooled EAC (early+late, n=100) / EXEC (mean share of six) / floor (first trigger off in control). Half-up rounding.
  GPT-4o-mini: NONE 3/2/10, BANK 32/20/6, RETR 32/13/10, SUMM 32/22/12, RWIM-LEDGER 29/32/40, SCHED 24/32/4. BANK vs SCHED 17 vs 9 (p=0.17).
  DeepSeek:    NONE 1/1/2,  BANK 45/35/6, RETR 33/16/8,  SUMM 25/16/6,  RWIM-LEDGER 10/36/6,  SCHED 7/33/6.  BANK vs SCHED 39 vs 1 (p<1e-8).
  Llama:       NONE 38/22/36 (idle switching, as at load 1), BANK 34/30/4, RETR 44/20/12, SUMM 11/23/4, RWIM-LEDGER 17/26/4, SCHED 18/26/4. BANK vs SCHED 18 vs 2 (p=0.0004).
  Gemini-FL:   NONE 2/1/4,  BANK 36/24/6, RETR 27/9/6,   SUMM 8/12/6,   RWIM-LEDGER 7/15/18,  SCHED 4/15/6.  BANK vs SCHED 33 vs 1 (p<1e-8).
  RWIM-LEDGER vs SCHED: no difference on any actor (12/7, 6/3, 4/5, 5/2). Fabrication floor persists under load (mini 40%, Gemini 18%).
Reading (replaces F53): the rewrite holds on DeepSeek and Gemini, is reduced on Llama (18 vs 34, now significant at 50 seeds), gone on mini (24 vs 32, p=0.17).
Exposure: 43-53% of the six triggers ever come into view; exec|seen under SCHED 68/65/60/31% (mini/DeepSeek/Llama/Gemini) vs 95/93/90/66% at one intention.
Also: RWIM-LEDGER load curve (loads 2-5, 20 seeds, both actors) filled in; figs/fig_load_ledger.pdf. Paper figure fig_load is SCHED only (user's choice).
Simulator note (F54) unchanged. Paper: Table 2 six-intention columns final (no dashes; Llama NONE dagger at six), Load paragraph, abstract, intro, discussion, conclusion updated; suite count 400 load 4-6 episodes.
Figure 1: three versions tried (frames+text v1, panel style v2, icon cards v3); user rejected v2/v3 as generic. Pending: real-frame storyboard (figs/fig_storyboard_thor.png) vs hand-drawn. v3 currently in main.tex; body ~30 lines over 8 pages with it.

**F56 (2026-10-06) — full-context control: the six-step window is not the cause.** run_queue_fullctx.sh, results/llm_or_{gpt4omini,gemini}_fullctx.csv
NONE design with --window 40 (whole transcript in context: briefing at step 0 and the cancel message at step 3 visible at every step), main cell, seeds 0-19, four variants.
  GPT-4o-mini: EAC 20/40 = 50% (early 10/20, late 10/20) | EXEC 18/20 = 90% | floor 5/20. Paired vs BANK(w6) 5 vs 8 (p=0.58); vs SCHED(w6) 18 vs 0 (p<1e-4).
  Gemini-FL:   EAC 19/40 = 48% (early 11/20, late 8/20)  | EXEC 11/20 = 55% | floor 3/20. Paired vs BANK 9 vs 9 (p=1); vs SCHED 18 vs 0.
Reading: with everything in context the LLM actor still acts on the withdrawn instruction about half the time, same as BANK; the rule actor (F7) goes to 0 at large windows, LLMs do not. Consistent with TriggerBench (full context, >50% keep reminding) and PM-Bench (full week in context per sim/pm_bench.py, no truncation; updated-task hit rate <=47%).
Paper: new paragraph "Full context" in 5.4; sentence in 4.1 pointing to it. Cost ~$1 for 160 episodes.
