# embodied_pm — Prospective Memory in a 3D Simulator

**One sentence.** FindingDory's arena (embodied 3D, execution-graded) + PM-Bench's task
tense (instruction arrives *before* its trigger, must survive distraction and revocation)
+ RWIM's mechanism (a memory coroutine that decides *when* to resurface the intention).

Started 2026-08-05. Sequel to the text-world pilot in `../pm_bench/`.

## Why AI2-THOR first (not Habitat)

- pip-installable on macOS, no GPU build, no multi-GB scene downloads;
- native object *states* (Toaster/Faucet/Microwave toggle on/off) — exactly what the
  event engine needs to change the world behind the agent's back and what world-state
  adjudication needs to grade;
- Habitat/HSSD (FindingDory's stack) stays the scale-up target for multi-room monitoring
  cost; noted as stage 2. ProcTHOR is the multi-room middle step.

## Design (mirrors lecture/大纲_v2.md appendix)

One episode:
1. **Briefing** (step 0): foreground chores (pick-and-place, FindingDory-style, they are
   the *distraction*) + one deferred intention: "If you ever see the toaster on, turn it
   off." Condition false at briefing time.
2. **Event engine** (scripted, seeded): at step E, toggles the trigger object on via
   `forceAction` while the agent is (typically) elsewhere. World changes out of view.
3. **Noticing** is instrumented: THOR's per-object `visible` flag (in frame + within
   visibilityDistance) is logged every step → first_visible_step.
4. **Adjudication**: end-of-episode world state. Toaster off after having been on, after
   first visibility, within the episode → executed. No menus anywhere.
5. **Cancellation mirror**: same seed, a mid-episode message "forget the toaster thing"
   at step C. Executing anyway = `executed_after_cancel` (the number no benchmark reports).

Knobs: delay E, cancel timing C (early/late), intention load k, context window W
(actor sees only last W steps → the briefing *evicts*; reproduces the text pilot's
eviction manipulation in 3D).

## Agents

- `oracle` — privileged; reads the event log; validates every episode is solvable
  (FindingDory/PM-Bench methodology).
- `negligent` — scripted; does chores, never monitors. Floor.
- `patroller-k` — scripted; detours to look at the trigger object every k steps.
  Mechanical cost-compliance frontier without any LLM.
- `llm` — Claude actor, text-rendered privileged observations, sliding context window W;
  memory policies:
  - `none`     — intention only in the briefing (dies with the window),
  - `bank`     — external intention store always in view (always-inject),
  - `rwim`     — RWIM-style coroutine: watches trajectory, keeps a bank
                 (status/knowledge/procedural + intentions), each step decides
                 note-or-silence; note is injected into the actor's next prompt.

## Status / runbook

- `python3 run_pilot.py --smoke` — 1 oracle + 1 negligent episode, no API needed.
- `python3 run_pilot.py --policy oracle --episodes 5` — solvability audit.
- `python3 run_pilot.py --policy patroller --k 6 --episodes 5` — scripted frontier.
- `python3 run_pilot.py --policy llm --mem rwim --episodes 5` — needs API credits
  (fail-fast on credit errors; as of 2026-08-05 credits are EXHAUSTED, runs queued).

CSV rows land in `results/`. Every episode seeded and replayable.

## Design lessons (overnight 2026-08-06, 1050+ episodes)

1. **Cancellation timing must be defined relative to response latency.** A cancel
   delivered after the fastest possible execution tests nothing (the deed is
   done); `eac_strict` counts only executions strictly after delivery, validated
   by deaf-patroller probes (caught 88-100%) vs honest agents (0%).
2. **Single-room kitchens saturate easy conditions.** Visibility and focality
   effects only emerge at delay>=10; multi-room (ProcTHOR) is the next
   separation lever.
3. **Focality has two components**: on-the-errand-route (controlled: 88.5 vs 40%,
   54.2 vs 0%) and ambient placement geometry (Toaster: off-route yet 84%).
   Both are designable knobs; `trigger_on_route` is logged per episode.
4. **Run overnight batteries under `caffeinate -is`** — App Nap froze Unity for
   ~2.7h. True throughput on this Mac: ~1 s/episode, ~2000 episodes/hour.
5. **Proximity is not execution.** Pass-by transit within the exec radius scored
   negligent agents at 50%; execution must be arrive-AND-declare (the nav-world
   analog of THOR's toggle action). Honest floors then read exactly 0.
6. **In-flight revocation needs handling.** A cancel that arrives mid-response
   must abort the leg; scripted agents that didn't were falsely flagged 17-21%.
   (Kept as a future LLM probe: does the model brake mid-route on "never mind"?)
7. **Patrol interval k must exceed one patrol leg's travel time** in large
   scenes, else the agent thrashes between goals and does nothing.

## Habitat line (pm_habitat.py)

habitat-sim 0.3.1 osx-64 under Rosetta (`~/miniforge3-x86`, env `habitat`);
test scenes in `data/scene_datasets/habitat-test-scenes/`. Multi-room
apartment_1 + skokloster-castle. Headline: periodic patrolling is strictly
dominated by incidental noticing in multi-room space (fig_crosssim.png) —
where-and-when-to-look becomes the scheduling problem. Run:
  source ~/miniforge3-x86/bin/activate && conda activate habitat
  python pm_habitat.py --policy oracle --episodes 5 --out results/habitat3.csv
8. **A rule-based window-bounded mock actor** flushes out every information-boundary leak (in-flight aborts, injection timing) before any LLM spends a token.
