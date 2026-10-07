# Mila / Anthropic credits application — text for our sub-project (2026-09-21)

The PI is merging several projects into one application, so everything here is short.
Sub-project title: **Revocable Memory for Embodied LLM Agents**

## SHORT VERSION — Section 2 (Project Description)

**Revocable memory for embodied LLM agents.** Agents are routinely given instructions to carry out later ("if you notice the coffee machine is on, turn it off"), and users change their minds. We built EPM-Bench, which tests this in two embodied simulators (AI2-THOR, Habitat) using matched twin episodes and deterministic grading from world state, with the memory design as the independent variable. Across about 5,000 episodes and six model families, including Claude Sonnet 5, common memory designs make agents keep executing a cancelled instruction in 55 to 64 percent of episodes (33 percent for frontier models). Storing the intention as a status-tracked entry that is rewritten on cancellation reduces this to 7 percent or less on every model. This is a controllability problem that grows with memory quality, and it aligns with Mila's work on LLM agents, embodied AI and AI safety. Frontier models are the part of the design we cannot afford: we could run them on only one fifth of it. All data are simulated. The 7,564-episode suite, code and traces will be released.

## SHORT VERSION — Section 3, item 6 (Objectives and Milestones)

(1) Run the full design on the Claude family, Haiku 4.5 to Opus 5, to see how the failure scales with capability (November 2026). (2) Test whether Claude, acting as the agent's memory manager without privileged information, can keep the record of intentions itself. Our current non-privileged version avoids violations but executes only a quarter of live instructions (December 2026). (3) Replicate the main result with Claude perceiving rendered frames, which small vision models could not do (January 2027). (4) Extend from revoked instructions to revoked information ("forget what I told you"), including forged requests from a third party (February 2027). Core paper submitted to AAMAS 2027 in October 2026, extended version for IJCAI 2027 or NeurIPS Datasets and Benchmarks, public release by March 2027.

## Item 7 (Permanent Community Deliverable)

EPM-Bench, an open benchmark for deferred and revoked instructions in embodied LLM agents: a frozen suite of 7,564 twin episodes in AI2-THOR and Habitat, a deterministic grader that reads world state (no LLM judge), reference implementations of six memory designs, and the full per-step traces of every model we evaluate, Claude models included. Released under a permissive licence with a leaderboard, so that new memory systems can be tested on the same episodes.

## Item 8 (Budget for this sub-project)

CAD 10,000

## Item 9 (Budget Justification)

One episode is 40 to 60 model calls. On Claude Sonnet 5 this costs about USD 0.20 in the text tier and about USD 0.70 with images. Paying out of pocket, we could run frontier models on only one fifth of the design (20 seeds, cancellation twins only). The request covers the full design on three Claude models in both simulators (about USD 1,300), Claude as the agent's memory manager across several designs and actors (USD 800), the pixel tier, which small vision models cannot do at all (USD 2,000), and the extension to revoked information (USD 600), plus 30 percent for development runs. This is about 8,000 episodes and 0.8 billion tokens. The questions are specifically about frontier models, so cheaper models cannot substitute.

Budget basis (internal note, not for the form): measured Sonnet 5 text tier ~USD 0.20/episode (85k tokens); pixel tier scaled from gpt-4o-mini's measured 385k tokens/episode; sum USD 4,700 x 1.3 = USD 6,100 = ~CAD 8,400, rounded to CAD 10,000.

---
# LONG VERSION (kept for reference)

## Section 2 — Project Description (Scientific Merit, Impact, and Innovation)

**Remembering Not To: do embodied LLM agents stop acting on instructions that were revoked?**

Household and workplace agents are routinely given instructions to carry out later ("if you ever notice the coffee machine is on, turn it off"), and users routinely change their minds. Psychology calls the ability to hold such an instruction and act on it when its cue appears *prospective memory* [1], and theories of practical reasoning treat the ability to drop a commitment as part of what an intention is [2]. Research on agent memory is almost entirely retrospective: it asks what an agent can recall, not whether it acts, or refrains from acting, at the right moment [3, 4]. This is a safety question. An agent that keeps executing an instruction after the user cancelled it is an agent the user does not control, and the better its memory, the worse the problem.

We have built EPM-Bench, which measures this in two embodied simulators, AI2-THOR [5] and Habitat [6]. An episode gives the agent a deferred instruction, fires its trigger out of the agent's view, and may cancel the instruction first. Every episode ships as four matched twins (no instruction, instruction, early cancellation, late cancellation), so differences are attributable to the instruction alone. Grading is deterministic and reads the state of the world, never the agent's words, so no LLM judge is involved. The memory design is the independent variable.

Results so far cover about 5,000 episodes and six model families, including Claude Sonnet 5. Without a memory pipeline no model executes the deferred instruction. With memory designs in common use, agents execute it and then keep executing it after cancellation: in 55 to 64 percent of episodes when the original instruction is re-injected (33 percent even for frontier models), 38 to 45 percent with retrieval memory, and 15 to 32 percent with a rolling summary. Storing the intention as an entry with a status, rewritten on cancellation, brings this to 7 percent or less on every model while live instructions are still executed at comparable rates. Across 480 matched twin pairs there is not one in which only the status-tracked design fails, and the pattern replicates in Habitat (36 of 49 violations against 0 of 49). The fix is fragile in instructive ways: a cancellation note that restates the original instruction loses most of the benefit, and placing the status-tracked entry in a retrieval store gives none. Concurrent work reports related failures of revocation in text and tool-use agents [7, 8, 9]. To our knowledge ours is the first to measure it for self-initiated, cue-driven actions in embodied environments, graded from world state.

**Alignment.** The project joins three of Mila's core areas: language-model agents, embodied AI, and the safety and controllability of AI systems. It builds on the applying group's work on foundation agents [4], embodied instruction following, and memory mechanisms for LLM agents.

**Why Claude.** The open questions concern frontier models, which we could afford to run on only one fifth of the design. We need Claude to ask whether the failure shrinks with capability within one model family, whether a strong model can act as the agent's memory manager without privileged information, and whether the results hold when the agent perceives pixels, which the small vision models we tried could not do.

**Data.** All data are simulated. No human subjects or personal data are involved. The frozen suite has 7,564 episodes (6,000 in AI2-THOR, 1,564 in Habitat) and will be released with code, prompts and per-step traces.

**References**
[1] Einstein, G. O., McDaniel, M. A. Normal aging and prospective memory. *J. Exp. Psychol.: Learning, Memory, and Cognition*, 1990.
[2] Bratman, M. E. *Intention, Plans, and Practical Reason.* Harvard University Press, 1987.
[3] Sumers, T. R., Yao, S., Narasimhan, K., Griffiths, T. L. Cognitive architectures for language agents. *TMLR*, 2024.
[4] Liu, B., et al. Advances and challenges in foundation agents. arXiv:2504.01990, 2025.
[5] Kolve, E., et al. AI2-THOR: an interactive 3D environment for visual AI. arXiv:1712.05474, 2017.
[6] Savva, M., et al. Habitat: a platform for embodied AI research. *ICCV*, 2019.
[7] Yao, C., et al. Forgetting without restarting: execution-state unlearning for stateful LLM agents. arXiv:2609.04875, 2026.
[8] Shen, Y. T., Toyoda, K., Leung, A. Revoked but still authoritative: an empirical study of revocation enforcement in agent-memory systems. arXiv:2609.08258, 2026.
[9] Liu, G., Gabriel, S. PM-Bench: evaluating prospective memory in LLM agents. *COLM*, 2026. arXiv:2607.12385.

---

## Section 3 — Project Objectives and Key Milestones

**Objective 1. How does the failure scale with capability?** Run the full design (three memory designs, four twins, fifty seeds, both simulators) on the Claude family, from Haiku 4.5 to Opus 5. Today our frontier rows rest on twenty seeds and cancellation twins only.
*Milestone, November 2026:* complete main table for three Claude models with matched-pair statistics.

**Objective 2. Can a capable model keep the ledger itself?** Our status-tracked store uses the true cancellation time, so it is an upper bound, not a method. The non-privileged version, where a second model call maintains the record of intentions, avoids violations but executes only about a quarter of live instructions. We will test Claude as memory manager for weaker and stronger actors, varying what the manager sees and how its reminders are worded.
*Milestone, December 2026:* a memory-manager design that reaches the upper bound on both violation and execution, or a clear account of why it cannot.

**Objective 3. From symbolic observations to pixels.** The small vision models we tested could not read an appliance's on or off state from a 320 by 240 frame, so the pixel tier could not separate memory designs.
*Milestone, January 2027:* the main contrast replicated with Claude perceiving rendered frames in AI2-THOR.

**Objective 4. From revoked instructions to revoked information.** When a user says "forget what I told you about the medication", does the agent's behaviour change, and who is allowed to make it forget? We will test the wording of the request, and forged requests from a third party aimed at a safety instruction, in the same twin design.
*Milestone, February 2027:* benchmark extension with results on at least four model families.

**Objective 5. Publish and release.** Core benchmark paper submitted to AAMAS 2027 in October 2026. Extended version with Objectives 1 to 3 for IJCAI 2027 or the NeurIPS Datasets and Benchmarks track. Public release of benchmark, code, prompts and traces under a permissive licence by March 2027.

**Expected usage.** One episode is 40 to 60 model calls and about 60,000 tokens in the text tier, several times that with images. Objectives 1 to 4 amount to roughly 6,000 Claude episodes, on the order of 0.5 billion tokens, mostly on Sonnet-class models.
