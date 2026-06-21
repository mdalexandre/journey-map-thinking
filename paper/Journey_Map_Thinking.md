# Journey Map Thinking: A Persistent Navigation Layer for Long-Running AI Agents

**Mario da Silva Alexandre** · DLux Digital, Tampa, Florida · [sincllm.com](https://sincllm.com)

---

honest_scope: PROVISIONAL_PAPER_DRAFT_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false

---

## 1. Abstract

An agent that has run for twenty minutes can produce polished prose, fill a directory with logs, and still have made no progress: it has lost its journey position, and no existing reasoning method, memory system, or tool library restores it. **JMT is a deterministic, LLM-free navigation layer designed to address journey-position loss by interleaving five typed checkpoints into an existing agent pipeline.** This paper introduces Journey Map Thinking (JMT), a deterministic, LLM-free navigation layer that interleaves five structured checkpoints into an existing agent pipeline intended to maintain journey position across runs. At its core, JMT is a prompt technique: the agent reads a structured, frozen position record before each pipeline stage and uses it to self-verify its own progress, giving itself a re-readable anchor that persists across sessions. The reference implementation is approximately 2,017 lines of Python and ships with a formal algorithm and an evaluation methodology comprising 11 metrics and hypotheses. Two tiers of empirical evidence are now in hand. First, the software mechanism: 26 of 26 unit tests pass (exit code 0), independently reproduced by a non-Claude Codex toolchain against the same 11 files and 2,017 lines, with four behavioral probes firing as specified (relevance suppression on trivial inputs, anti-loop warning on status-only requests, mandatory concrete-slice selection on vision-scope inputs, and BLOCKED_NO_PROGRESS on summary-only runs). Second, the frozen-position anchor: tested in its target post-compaction regime in a pre-registered, powered, cross-model A/B study (96 trials, 48 per arm, haiku/sonnet/opus agents, blind judging on sonnet), returning no statistically significant next-action-recovery benefit over Claude Code's own /compact mechanism (correct-next-action delta 0.000, Fisher exact p=1.000; held-place delta +0.042, p=0.819). The real /compact already preserves the committed next step in dedicated summary sections, making the anchor redundant for that recovery regime. The broader 11-metric project-level study (M1 through M11) has not been run and remains future work. One honest negative finding is also included: the positioner returned relevance=low and an empty lane list on the task of writing this paper, exposing a concrete marker-vocabulary gap.

---

## 2. Introduction

You have watched an agent loop for twenty minutes, producing careful analysis and well-formatted plans, advancing nothing. The problem is not that the agent reasoned poorly or lacked tools. The problem is that it had no principled answer to four questions: which lane does this task belong to, which milestone is the target, has the gate been satisfied, and what concrete artifact proves progress?

**JMT is a deterministic, LLM-free navigation layer addressing journey-position loss: the state in which an agent cannot answer which lane, milestone, or gate applies to its current run.** A second scenario makes the stakes concrete from a different angle. A practitioner hand-off begins: the previous run claimed progress, the handoff note says "done," and the next run spends its entire budget reconstructing what was actually completed. No file changed. No gate was checked. The claim of progress was real to the agent that made it, and false to every downstream stage that depended on it. The cost is not the wasted run. The cost is the accumulated drift between what the agent believes about its own state and what is true, a gap that widens silently across runs until a human intervenes to reset the context.

Chain-of-thought prompting [1] and ReAct [2] improve step-level reasoning and action interleaving. Reflexion [3] adds verbal self-critique within a session. Tree of Thoughts [4] enables deliberate multi-path search. AutoGen [5] orchestrates multi-agent conversation for complex tasks. Yet a recurring failure mode persists in long-running pipelines: the agent loses track of where it is in the overall journey.

This failure is distinct from the problems that reasoning methods, memory systems, or tool libraries address. An agent can hold a detailed plan, access prior conversation history, and have the correct tools available, and still fail because it does not know which capability lane the current task belongs to, which milestone within that lane is the target, whether the gate condition for that milestone has been satisfied, or what concrete artifact is required as proof of progress. Without this navigation state, agents enter progress-free loops, repeat steps already completed in prior runs, claim progress on summaries rather than artifacts, and silently block on actions that require human authorization.

We introduce Journey Map Thinking (JMT), a persistent navigation layer that addresses this gap. JMT is not a planner, a reasoning method, a memory system, or a multi-agent framework. It is a control-state layer that wraps an existing pipeline, inserting five deterministic checkpoints that read and write typed navigation artifacts: a position record, a lane selection, a gate alignment, a progress check, and a map update. The pipeline host remains the completion authority; JMT adds the navigation context.

For ML and agent-engineering readers: navigation position (which lane, which milestone, which gate) is an orthogonal coordinate to reasoning quality. A model that reasons correctly within a turn can still be in the wrong lane, targeting a completed milestone, or satisfying a gate that no longer applies. JMT tracks the orthogonal coordinate; reasoning methods track the other.

The contributions of this paper are:

- A formalization of the journey-position-loss problem as a distinct class of agent failure, with four named observable failure modes and four design requirements for a navigation layer.
- The Journey Map Thinking framework: a conceptual model comprising North Star, Journey Lanes, Milestones, Gates, Blockers, Unlock Artifacts, Progress Types, Capability Levels, Journey Position, and Journey Map Updates, with ten formal definitions grounded in real code vocabulary.
- A reference implementation of approximately 2,017 lines of deterministic Python across eleven files, installed and tested in the quark-studio repository, with a 5-subcommand CLI, a 7-artifact protocol, and a test suite.
- Empirical evidence on two layers: (a) the software mechanism verified by two independent toolchains (26 of 26 tests pass, exit code 0, on both a Claude-based run and a non-Claude Codex reproduction against the same 11 files and 2,017 lines; four behavioral probes fire as specified); and (b) the frozen-position anchor tested in its target post-compaction regime in a pre-registered, powered, cross-model A/B (48 trials per arm, 96 total) that returned a null against Claude Code's own /compact (the anchor adds no measurable next-action-recovery benefit over /compact, which already preserves the next step in dedicated summary sections).
- An evaluation methodology with 11 operationally defined metrics and hypotheses H1 through H11, proposed as a blueprint for future empirical study.
- An honest negative finding: the deterministic positioner returns relevance=low and an empty lane list when given the task of writing this paper itself, demonstrating a concrete marker-vocabulary coverage gap.

To our knowledge, the framing of long-horizon agent failure as navigation-position loss, with a typed, gate-checked, artifact-anchored navigation layer as the proposed remedy, represents a novel direction for the agent engineering community. We make no claim of empirical superiority over any existing system. The software mechanism is empirically verified and the frozen-position anchor has been tested to a null against Claude Code's own /compact; the broader 11-metric project-level evaluation (M1 through M11) remains future work.

The term "Journey Map" names the broader program of which JMT is one member. The program comprises the deterministic navigation substrate (the journey_map package), the pipeline stages between which journey_map CLI checkpoints are interleaved (go_loop and latent_ambition as always-active pipeline stages; dynamic_prompt_tailor and book_procedures as flag-gated stages in quark-studio), and the agent-facing cognitive discipline that ties them together: the practice of reading and holding the frozen position artifacts as a reference before acting. This paper formalizes the navigation-substrate and agent-facing-discipline member of that program, which we call Journey Map Thinking. The remaining members are described by their own documentation; this paper does not claim to cover the full program.

We ask skeptical reviewers to engage with the proposed evaluation methodology as a blueprint, not a result, and to consider whether the navigation-position-loss framing names a failure class worth formalizing.

The remainder of this paper follows a three-part arc. The failure mode we identify (Sections 3 and 4) is distinct from planning errors, memory loss, and tool gaps. The framework, algorithm, and one grounded case study (Sections 5 through 11) provide the architecture and formal procedure for addressing it. The design trade-offs, limitations, and evaluation blueprint (Sections 12 through 18) scope the honest boundary of the contribution.

---

## 3. Background and Related Work

### 3.1 Service Design Origins: Journey Mapping and Service Blueprinting

The term "journey map" originates in service design. Shostack [6] introduced the service blueprint as a structured diagram of service delivery stages, touchpoints, and failure points, enabling systematic analysis of complex service processes. Bitner, Ostrom, and Morgan [7] formalized service blueprinting as a practical innovation tool, emphasizing the mapping of customer actions, frontstage and backstage activities, and support processes at each stage. Lemon and Verhoef [8] extended this to the full customer journey, distinguishing pre-purchase, purchase, and post-purchase phases and identifying touchpoints where experience can be measured and improved.

JMT borrows the structural insight from service blueprinting: a complex, multi-stage process can be made tractable by identifying named stages (here, lanes and milestones), the conditions for transitioning between them (gates), the obstacles that prevent transitions (blockers), and the artifacts that prove completion. JMT does not claim to be a service blueprint or a customer journey map; it adapts the lane-and-touchpoint abstraction to the domain of agent pipeline execution, where the "customer" is the agent run and the "service stages" are the lanes, milestones, and gates of a system-level North Star.

### 3.2 LLM Agent Reasoning Methods

Step-level reasoning methods improve what happens within a single turn but leave the agent's cross-run position unaddressed. Chain-of-thought prompting [1] elicits step-by-step reasoning from LLMs, improving performance on multi-step reasoning tasks. ReAct [2] combines reasoning traces with actions, allowing agents to interleave thought and tool use within a single turn. Tree of Thoughts [4] structures reasoning as deliberate search over a tree of intermediate thoughts, enabling backtracking. Plan-and-Solve prompting [9] decomposes tasks into a plan phase followed by a solve phase, improving zero-shot chain-of-thought performance.

ML practitioners and agent engineers face this gap acutely: production SWE-bench agents, tau-bench loops, and long-horizon ML pipelines run across multiple processes, container restarts, and checkpoint boundaries, none of which carry cross-run navigation state by default. Memory systems (MemGPT [10]) and agent frameworks (AutoGen [5]) persist conversation history and orchestration state, but neither records which capability lane the agent is currently targeting, which gate must pass, or which named blocker is preventing advance. Navigation-position loss is therefore additive to the challenges these systems address, not redundant with them.

These methods operate at the level of single-step or single-session reasoning. JMT operates at a different level: it tracks the agent's position across pipeline runs, not within a single reasoning trace. A step-level reasoning improvement and a cross-run navigation layer are complementary, not competing.

### 3.3 Reflexive and Iterative Agents

Reflexion [3] enables language agents to learn from prior attempts by storing verbal reflections in an episodic memory and using them to condition future attempts. Self-Refine [11] applies iterative self-feedback within a session to improve outputs across successive refinement rounds.

Both systems improve output quality by iterating on a prior attempt. JMT differs in that it tracks persistent structured state (lane, milestone, gate, blocker) across pipeline runs, not just the quality of the most recent output. A progress check that returns progress_made=False and recommends BLOCKED_NO_PROGRESS is not a quality critique; it is a navigation signal that the run did not advance the journey, regardless of output quality.

### 3.4 Long-Horizon and Open-World Agents

Voyager [12] is an open-ended agent for Minecraft that builds a skill library through exploration and curriculum, enabling lifelong learning. The AI Scientist [13] automates the research pipeline from idea generation through experiment execution to paper writing. Both systems face the navigation problem: how does an agent know where it stands in a long-horizon objective and what to do next?

JMT does not solve long-horizon autonomy (see Section 13). It proposes a navigation layer that makes the agent's position in a predefined lane taxonomy explicit and persistent. The 14 lanes and their milestones must be manually authored; the system does not discover new lanes on its own. Generalizing JMT to open-world lane discovery is a future work item (Section 16).

### 3.5 Multi-Agent Systems

AutoGen [5] provides a framework for multi-agent conversation, enabling groups of agents with complementary roles to collaborate on complex tasks. JMT is designed for a single-pipeline agent, not for multi-agent orchestration. The journey map is a per-pipeline navigation state; extending it to a shared map across parallel agent tracks is a future work item (Section 16).

### 3.6 Agent Memory and Skill Libraries

Position state, not episodic memory, is the axis that separates JMT from this cluster of systems. MemGPT [10] treats LLMs as operating systems with virtual context, enabling long-context reasoning through hierarchical memory management. Generative Agents [14] simulate human behavior in a social environment using memory streams, reflection, and planning. Voyager [12] accumulates a skill library of verified executable code, allowing the agent to reuse prior capabilities.

JMT tracks position and blockers, not episodic conversational memory or social simulation. It is closer to a navigation state than to a memory store, though it does append a persistent history (journey_history.jsonl) of completed runs. The distinction is that JMT tracks where the agent is and what gate must be passed, not what the agent has said or experienced in prior conversations.

### 3.7 Agent Evaluation Benchmarks

AgentBench [15] evaluates LLMs as agents across eight environments spanning web browsing, operating system interaction, and games. SWE-bench [16] measures an agent's ability to resolve real-world GitHub issues. WebArena [17] provides a realistic web environment for autonomous task completion. GAIA [18] benchmarks general AI assistants on real-world tasks requiring tool use and reasoning. tau-bench [19] evaluates tool-agent-user interaction in retail and airline domains.

These benchmarks measure task success rate, but not journey-position awareness. Concretely, SWE-bench scores whether a GitHub issue was resolved; tau-bench scores tool-agent-user interaction outcomes; GAIA scores task completion on real-world problems: none records which lane the agent was in, whether it was targeting the correct milestone, or whether a gate condition was satisfied before the agent moved on. None of them measure whether an agent knows which lane it is in, whether it is making progress toward a gate, or whether a blocker has been surfaced and named. A JMT-specific evaluation methodology is needed, as described in Section 12.

### 3.8 Programmatic Pipeline Control

DSPy [20] compiles declarative LLM pipelines into self-improving chains by optimizing prompts and module compositions. Toolformer [21] teaches language models to use tools through self-supervised API call learning.

JMT is neither a compilation layer nor a self-teaching mechanism. It is a navigation wrapper: a deterministic, LLM-free layer that reads and writes structured navigation state at five points in an existing pipeline. It does not optimize the pipeline; it provides position awareness to the agent and the pipeline host. DSPy acts before the pipeline runs, optimizing prompt and module composition at compilation time; JMT acts during and after each pipeline run, recording navigation state that persists across runs regardless of prompt composition.

---

## 4. Problem Statement

### 4.1 The Journey-Position-Loss Problem

Consider a long-running AI agent executing a multi-step pipeline that is intended to advance a system toward a declared goal (the North Star). At any given stage of the pipeline, the agent must be able to answer four questions:

1. Which lane of work does this task belong to?
2. Which milestone within that lane is the current target?
3. Has the gate condition for that milestone been satisfied by prior work?
4. What concrete artifact proves that progress has been made?

When the pipeline has no navigation layer, these questions have no principled answers. The agent proceeds based on the immediate task description and the available context, without any persistent, structured record of its location in the journey. We call this state "journey-position loss."

Formally, let a journey position be a tuple (relevance, level, lanes, blockers) where relevance describes the current task's connection to the North Star, level is the current provisional capability level of the relevant component, lanes is the set of applicable journey lanes, and blockers is the set of named obstacles that prevent advancement. Journey-position loss occurs when any element of this tuple is unknown to the executing agent at the time it acts.

### 4.2 The Frozen Position Anchor

Consider, as a motivating analogy, how a person navigating a complex multi-day task manages their place in it. A person can, at any moment, recall a frozen snapshot of where they left off: which stage they were on, what was already done, and what remains. This recallable snapshot gives them a stable anchor. They do not re-derive their position from scratch at the start of every work session; they consult a known reference point and resume from there.

An agent executing a long-running pipeline has no equivalent by default. Without a persistent, re-readable record of its position, the agent must reconstruct context from the raw history each time, a process that is imprecise, expensive, and failure-prone. As the pipeline runs lengthen and the number of completed steps grows, the probability that the agent correctly reconstructs its position from prose history alone decreases.

This is the motivation behind Journey Map Thinking. JMT gives the agent a frozen position: a typed, file-backed snapshot of its lane, milestone, gate status, and blockers, written at the end of each pipeline run and re-read at the start of the next. The agent does not need to infer its position; it reads the artifact. The position is frozen in the sense that it is not recomputed on each read; it is written once per run (deterministically, by the position and update subcommands) and held stable until the next run updates it.

This frozen-anchor design is what makes JMT a prompt technique as well as a navigation substrate. The agent is expected not merely to produce the position artifacts, but to read them before acting, using them as a structured self-verification check: "where am I, what gate must I pass, and did the last run actually advance the journey?" The no-progress guard (Section 9.4) enforces the last question mechanically, but the first two are answered by the frozen artifacts that JMT provides.

The theorized value of the frozen anchor is precisely in the genuine-memory-loss regime: after compaction, or in a cross-session restart where no prior context survives. This paper tests that claim directly (Section 12.2). The honest result is that against Claude Code's own /compact mechanism, which already preserves the committed next step in dedicated Pending Tasks, Current Work, and Optional Next Step sections, the frozen anchor produces no measurable next-action-recovery benefit. All twelve /compact summaries in the powered A/B study named the committed step unambiguously, making the anchor redundant for that regime. The framework's verified value is therefore in the deterministic positioning, gating, and progress-refusal mechanism (Section 12.1), not in the anchor outperforming a strong compaction baseline. The anchor's remaining defensible ground is in regimes /compact does not cover: a brand-new session with no compaction summary at all, and structured long-horizon lane and gate positioning that a prose summary may not preserve. Neither regime was tested.

(Note: the human-navigation analogy above is motivational framing, not a neuroscience or cognitive-science claim. No assertion is made about memory consolidation or cognitive mechanisms. The analogy is used only to clarify the design intent behind the frozen-position abstraction.)

### 4.3 Observable Failure Modes

Journey-position loss produces four observable failure modes (these are proposed hypotheses about failure patterns, not measured results):

**(a) Infinite refinement without artifact.** The agent iterates on the quality of a generated document, plan, or summary without producing the concrete build artifact that the lane's gate requires. The output grows longer and more polished while the gate remains unmet.

**(b) Repeated-step execution.** Across multiple runs on the same task, the agent performs the same stage it performed in a previous run, without checking what was already completed. The what_not_to_repeat field in JMT's lane selection is designed to counter this pattern.

**(c) Prose-summary progress claim.** The agent claims progress because it has written a summary, a plan, or a status update, rather than because it has produced a changed file, passed a gate, added a test, or run a benchmark. The JMT progress check blocks this by requiring at least one concrete signal for progress_made to be true [OBSERVED from progress.py].

**(d) Blocker amnesia.** An action that requires owner authorization (such as enabling a system service or approving a production deployment) is attempted, fails, and the failure is not recorded as a named blocker. The same action is retried in subsequent runs without surfacing the need for human action. The JMT blocker_map.json is designed to name and persist blockers across runs.

### 4.4 A Concrete Negative Example

The journey-position-loss problem is not hypothetical for the system described in this paper, and the authors do not soften this finding. When the real JMT positioner was run on the task of writing this paper, the observed output was:

```
$ python -m qai_core.qah.journey_map.cli position --raw <this task> --output journey_position.json
OK: relevance=low lanes=[] owner_dependent=False anti_loop=False
```

[OBSERVED from live CLI run, grounding_notes.md Section 10]

The task of writing a research paper is a substantial, meaningful task. The positioner returned relevance=low and an empty lane list because the deterministic marker vocabulary has no entry for "research paper" or "write a paper." (Lane H covers "prose/article/essay/blog post" but not "paper.") This is a concrete example of failure mode (a) and (b) combined: a task that would benefit from navigation awareness is unmapped, and the pipeline has no way to know which lane or milestone to target.

### 4.5 Design Requirements for a Navigation Layer

A navigation layer that addresses journey-position loss must satisfy four requirements:

1. **Deterministic.** The navigation layer must not introduce a new LLM call that could itself produce a hallucinated or inconsistent navigation assignment. Routing must be predictable and auditable.
2. **Persistent.** Navigation state must survive across pipeline runs, so that a run can know what was done in prior runs and avoid repeating it.
3. **Honest.** The layer must actively block vague progress claims. A progress check that accepts "I wrote a summary" as progress would be worse than no check at all.
4. **Artifact-anchored.** Progress must be proven by a concrete, verifiable signal: a changed file, a passed gate, an added test, a run benchmark, a trained model, a completed dogfood run, or an owner-unlock packet.

---

## 5. Journey Map Thinking Framework

### 5.1 Overview

JMT solves a specific problem: the agent has no principled answer to the four coordinates of its journey position (as defined in Section 4.1): which lane (relevance), which capability level (level), which set of applicable lanes (lanes), and which named obstacles prevent advance (blockers). Journey Map Thinking (JMT) is a five-stage deterministic layer that interleaves structured navigation checkpoints into an existing agent pipeline. It does not replace the planner, the generator, the QA stage, or the stop gate. The pipeline host remains the completion authority. JMT adds persistent, typed, gate-checked position awareness that the pipeline would otherwise have none of (in the reference implementation, the /go pipeline in quark-studio; generalizability to other pipelines is untested, see Section 15.3). From the agent's perspective, JMT is a prompt technique: at the start of each run the agent reads the frozen position artifacts (journey_position.json, journey_lane.json) to self-verify its progress and orient itself before the pipeline begins.

The five JMT stages are: Positioning (after raw signal capture), Lane Selection (after latent ambition compilation), Gate Alignment (after planning), Progress Check (after QA), and Map Update (after release). Each stage runs a deterministic CLI subcommand and writes a typed artifact. No LLM call is made at any JMT stage; all routing is marker-matching against a fixed vocabulary.

### 5.2 The North Star

The North Star is the system-level declared intent against which all journey positions are measured. In the reference implementation [OBSERVED from schema.py and north_star.json]:

```
NORTH_STAR = "QAH as an Ambition-to-Reality Operating System"
```

The seeded north_star.json encodes the meaning of this declaration as a 6-step chain: (1) the human gives a small idea; (2) QAH understands the deeper ambition; (3) QAH writes the prompt it needs and executes it; (4) QAH builds real artifacts and verifies them; (5) QAH learns from failure and safely promotes components; (6) QAH pushes the journey forward.

A VISION meta-lane exists for pure-ambition asks ("push humanity forward", etc.) that must be resolved into a concrete first slice before work can proceed.

### 5.3 The Fourteen Journey Lanes

Fourteen journey lanes (A through N) partition the capability space of the system [OBSERVED from lanes.py]. Each lane tracks one real component, carries a provisional capability level, and enforces a claim boundary, an anti-overclaim rule that prevents asserting a property the lane cannot yet support.

| Lane | Name | Component | Level | Claim Boundary |
|------|------|-----------|-------|----------------|
| A | Recursive /go Prompt Loop | go_loop | L5_ASSISTIVE_READY | no autonomous code-execution claim; the agent executes |
| B | Latent Ambition Compiler | latent_ambition | L5_ASSISTIVE_READY | no claim of correct ambition without dogfood evidence |
| C | Goal-to-Gate Compiler | goal_to_gate_v3 | L3_TESTED | no metric-improvement claim without a measured before/after |
| D | Real Project Execution | project_builder | L4_SHADOW_READY | no done claim without an artifact-backed release verdict |
| E | Agent Run Reviewer | agent_run_reviewer | L4_SHADOW_READY | advisory only, no benchmark baseline yet |
| F | Specialist Model Foundry | model_foundry | L3_TESTED | no model-quality claim without a held-out baseline comparison |
| G | Claim-Audit / truth_auditor | reliability_harness | L5_ASSISTIVE_READY | no accuracy claim without a labeled fixture measurement |
| H | Generated-Prose Specialist | generated_prose_specialist | L3_TESTED | no quality claim without a rubric measurement |
| I | System Guardian Product | system_guardian | L4_SHADOW_READY | no prevention claim without a soak/pressure-event report (owner_dependent) |
| J | Open-World Runtime | open_world | L2_ARTIFACT_PRODUCING | no capability claim without a baseline comparison |
| K | Benchmark / Model Comparisons | beyond_gpt5 | L3_TESTED | no superiority claim without a fair, reproduced benchmark |
| L | Quantum Research Track | qllm | L2_ARTIFACT_PRODUCING | never claim quantum advantage; report calibrated deltas only |
| M | Production Activation | release_v1 | L1_CALLABLE | no production-ready claim without owner approval and rollback proof (owner_dependent) |
| N | Reflection / Memory | reflection | L3_TESTED | memory only from experience, never from a plan |

The claim boundary on each lane is not advisory; it is a structural constraint encoded in the lane definition and enforced by the gate alignment stage, which records blocked_claims in journey_gate_alignment.json.

### 5.4 Routing Logic

Lane assignment is deterministic [OBSERVED from lanes.py]: the positioner matches the raw task description against a marker vocabulary using a fixed precedence order:

```
MATCH_PRIORITY = (I, F, A, E, G, C, K, J, L, M, H, B, N, D)
```

This precedence ensures that specific markers (such as "Linux system guardian" routing to lane I) outrank generic markers (such as "build a" routing to lane D). When a task matches no lane, the positioner returns lanes=[] and relevance is set to low or none. Owner-dependent lanes (I and M) cause the selector to emit an owner-unlock packet and proceed with owner-independent work in parallel.

### 5.5 The Five-Stage Pipeline Placement

The five JMT stages sit at fixed points in the host pipeline [OBSERVED from cli.py and the installed SKILL.md]:

| After host phase | JMT stage | CLI subcommand | Output artifact |
|-----------------|-----------|----------------|-----------------|
| Raw signal capture | Positioning | position | journey_position.json |
| Latent Ambition Compiler | Lane Selection | select-lane | journey_lane.json |
| Planner | Gate Alignment | align-gate | journey_gate_alignment.json |
| QA/Evaluator | Progress Check | progress | journey_progress_check.json |
| Release Gate | Map Update | update | journey_map_update.md, journey_history.jsonl |

The feature flag QAH_GO_JOURNEY_MAP gates the entire JMT layer. When it is off, the pipeline is byte-for-byte unchanged.

### 5.6 Structural Position of JMT

JMT is a navigation and control-state layer around an existing pipeline. It is not a planner, not a generator, not a memory system, and not a reasoning method. Its role is to tell the pipeline where it is, which lane and milestone it targets, whether the gate has been met, and what the next unlock must be. A planner determines what work to do next; JMT records where in a predefined lane taxonomy the pipeline currently sits. An episodic memory system records what the agent said or experienced; JMT records position and progress signal. A reasoning method improves step-level inference within a turn; JMT operates between turns, recording whether the run advanced the journey at all.

Understood in this dual role, JMT is both the navigation substrate (the deterministic layer that writes the typed artifacts) and the prompt technique (the cognitive discipline by which the agent reads those artifacts, holds them as a frozen reference, and uses them to self-verify its progress before acting). The substrate is LLM-free and deterministic; the technique is the reading and consulting discipline that gives the agent its positional anchor.

See Figure 3 for the structural relationship between North Star, lanes, milestones, gates, and blockers.

### 5.7 Comparison on Shared Axes

The table below places JMT alongside the system classes surveyed in Section 3, on four axes that distinguish navigation-position tracking from other persistence and improvement mechanisms. All entries are mechanistic descriptions; no measured performance comparisons are implied.

A skeptical ML researcher may ask: why is a Python module (journey_map) the right unit here, rather than a prompt template that tells the agent to track its own lane? The answer has three parts. First, a prompt template is rewritten at each run's compilation time by the same LLM that may be disoriented; a deterministic Python module is not rewritten by the agent and cannot hallucinate a routing decision. Second, the gate alignment and progress check stages require concrete filesystem signals (changed files, gate verdicts, test coverage), not language-model outputs; encoding those checks in Python lets them serve as a hard exit-code contract that the pipeline host can act on mechanically. Third, the blocked_claims list in JourneyGateAlignment is the mechanism by which the navigation layer prevents the generator from making claims its current lane cannot support; a prompt template has no equivalent enforcement path. This does not mean a prompt template cannot produce similar behavior in some cases; it means the behavior would not be auditable, portable, or provably LLM-free. These are open engineering trade-offs, not proved superiority claims.

| System Class | Persistence Level | What It Tracks | Failure Mode Addressed | When It Acts |
|---|---|---|---|---|
| JMT (this work) | Cross-run, global | Navigation position: lane, milestone, gate status, blocker | Journey-position loss (Section 4.1) | After each of five named pipeline phases |
| CoT / ReAct / ToT (reasoning methods) | None (within a single turn) | Reasoning steps and action traces | Step-level reasoning quality | Within a single turn |
| Reflexion / Self-Refine (iterative refinement) | Session-level verbal memory | Quality of prior attempt (verbal critique) | Output quality on repeated attempts | Within a session, before the next attempt |
| MemGPT / Generative Agents (episodic memory) | Session or multi-session conversation history | What the agent said or experienced | Context loss across long conversations | Continuously, as conversation history accumulates |
| Voyager (skill library) | Cross-run skill programs | What the agent can do (verified executable programs) | Skill reuse across novel situations | When a new task requires a prior skill |
| DSPy (pipeline compiler) | Optimized prompt and module composition | Pipeline compilation and self-improvement | Prompt and module suboptimality | Before the pipeline runs (compilation time) |

```
North Star: "QAH as an Ambition-to-Reality Operating System"
 (stored in north_star.json; NORTH_STAR constant in schema.py)
 |
 +----------------------------------------------+
 | |
 Lane A (L5_ASSISTIVE_READY) Lane F (L3_TESTED)
 Recursive /go Prompt Loop Specialist Model Foundry
 component: go_loop component: model_foundry
 | |
 +-- Milestone: "self-prompt compiler" +-- Milestone: (active)
 | | | |
 | +-- Gate: | +-- Gate:
 | | artifact-backed release | | held-out baseline
 | | verdict required | | comparison required
 | | | |
 | +-- Blocker: (none active) | +-- Blocker:
 | | can_advance_now = true | "no trained specialist
 | | | checkpoint on disk"
 | +-- Unlock: next milestone | |
 | | next_unlock:
 | | "train or download
 | | a checkpoint"
 |
 Lane I (L4_SHADOW_READY, owner_dependent=true)
 System Guardian Product
 component: system_guardian
 |
 +-- Blocker: "earlyoom.service inactive;
 | owner action required"
 | owner_dependent = true
 | |
 | Owner Unlock Packet emitted
 | --> human action required

... Lanes B, C, D, E, G, H, J, K, L, N follow the same structure...
```

*Figure 3: Journey lane / milestone / gate model. Each lane tracks one real system component. Milestones are intermediate objectives; gates are pass/fail conditions; blockers surface what prevents advance. Owner-dependent lanes halt autonomous action [OBSERVED from lanes.py and artifacts.py].*

---

## 6. Formal Definitions

The following ten definitions are grounded in real code vocabulary; field names match the source dataclasses exactly. This is the ethos claim of the framework: every concept has a corresponding implementation artifact, and a skeptical reader can inspect the source files to verify each definition. All ten definitions are grounded in the real code vocabulary from the reference implementation [OBSERVED from schema.py, lanes.py, position.py, selector.py, gate_alignment.py, progress.py, artifacts.py].

**Definition 1: North Star.** A system-level declared intent string. In this implementation, NORTH_STAR = "QAH as an Ambition-to-Reality Operating System" [OBSERVED, schema.py]. Stored in north_star.json and encoded as a 6-step ambition-to-reality chain. The North Star provides the reference against which the north_star_relevance field of every JourneyPosition is assessed. A VISION meta-lane handles pure-ambition asks that must be resolved into a concrete first slice before any lane can be selected.

**Definition 2: Journey Lane.** A named, scoped partition of the capability space, each covering one real system component. A lane carries: an identifier (A through N), a human-readable name, the name of the real component it tracks, a provisional capability level (L0_CONCEPT through L10_AMBITION_TO_REALITY_OS), and a claim boundary (an anti-overclaim rule stating what cannot be asserted without evidence) [OBSERVED: 14 lanes defined in lanes.py]. Tasks are routed to lanes by deterministic marker-matching against a fixed precedence list MATCH_PRIORITY = (I, F, A, E, G, C, K, J, L, M, H, B, N, D). Formally, a claim c violates the claim boundary of a lane if c asserts a property that the lane's claim_boundary string explicitly prohibits; the gate alignment stage records such violations in the blocked_claims[] list of JourneyGateAlignment (Definition 4).

**Definition 3: Milestone.** A named intermediate objective within a journey lane, representing one meaningful increment of progress toward the lane's goal. Milestones are selected by the Lane Selection stage (select-lane subcommand) and stored in the selected_milestone field of JourneyLaneSelection (journey_lane.json). Example [OBSERVED from real journey_history.jsonl entry]: "self-prompt compiler" in lane A. A milestone is distinct from a gate (Definition 4) in that a milestone names a target state, while a gate names the verifiable condition that certifies that state has been reached; and distinct from a lane goal in that the lane goal is the terminal objective of the lane, while milestones are the intermediate waypoints selected by the select-lane stage for a single pipeline run.

**Definition 4: Gate.** A named pass/fail condition that must be satisfied before the journey can advance from the current milestone to the next. Encoded in JourneyGateAlignment (journey_gate_alignment.json) as: lane, release_gate, success_condition, failure_condition, planned_artifacts[], required_tests[], qa_checks[], and blocked_claims[]. A gate is aligned in the Gate Alignment stage (after the planner) and evaluated in the Progress Check stage (after QA). The gate passes when the QA verdict starts with "PASS" (PASS or PASS_WITH_WARNINGS) or the release verdict is PASS or PASS_WITH_WARNINGS [OBSERVED from progress.py].

**Definition 5: Blocker.** A named obstacle that prevents the current lane from advancing, stored in blocker_map.json as a lane-keyed entry carrying a description, an owner_dependent boolean, and a next_unlock string. Real examples [OBSERVED from blocker_map.json]: lane F carries "no trained specialist checkpoint on disk for some specialists" (owner_dependent=False); lane I carries "earlyoom.service inactive; owner action required" (owner_dependent=True, next_unlock: "owner enables earlyoom / approves resident service"); lane M carries "owner opt-in + production approval required" (owner_dependent=True). A blocker with owner_dependent=True halts autonomous action on that lane and triggers an owner-unlock packet.

**Definition 6: Unlock Artifact.** A concrete deliverable whose production satisfies a blocker and permits the journey to advance. Stored in the next_unlock field of JourneyProgressCheck (journey_progress_check.json) and in next_unlocks.json in the global map. When progress_made is False, next_unlock is forced to: "produce a concrete artifact or report a true blocker; never record a summary" [OBSERVED from progress.py]. For owner-dependent lanes, the unlock artifact is an owner-unlock packet emitted before the system halts autonomous action on that lane. Production of an unlock artifact is detected when at least one concrete signal from the set defined in the no-progress guard (Section 9.4) is present in the run that targeted the blocker, and the blocker's next_unlock description matches the artifact produced.

**Definition 7: Progress Type.** A categorical label classifying what kind of forward movement a run produced. One of 14 values [OBSERVED from PROGRESS_TYPES in schema.py]: BUILD_ARTIFACT, FIX_DEFECT, PASS_GATE, FAIL_GATE_WITH_UNLOCK, TRAIN_MODEL, RETIRE_MODEL, RUN_BENCHMARK, UPDATE_RUNTIME, CREATE_OWNER_PACKET, INTEGRATE_IN_GO, DOGFOOD_REAL_TASK, QA_VERIFY, REFLECT_LESSON, BLOCKED_NO_SAFE_ACTION. The last value is forced when no concrete progress signal is detected.

**Definition 8: Capability Level.** A provisional ordinal estimate of where a system component currently sits, on an 11-level scale [OBSERVED from CAPABILITY_LEVELS in schema.py]: L0_CONCEPT, L1_CALLABLE, L2_ARTIFACT_PRODUCING, L3_TESTED, L4_SHADOW_READY, L5_ASSISTIVE_READY, L6_SCOPED_PRODUCTION_READY, L7_REAL_PROJECT_OPERATOR, L8_OPEN_WORLD_MEASURED, L9_SPECIALIST_MODEL_OS, L10_AMBITION_TO_REALITY_OS. The code comment explicitly marks these as provisional estimates, not certified facts. Tasks off any lane receive the label NA_TRIVIAL_OR_UNMAPPED. A component advances from level Lk to Lk+1 when a pipeline run produces progress_made=True with progress_type in {BUILD_ARTIFACT, PASS_GATE, TRAIN_MODEL, RUN_BENCHMARK, DOGFOOD_REAL_TASK} and the run's milestone is assessed by a human reviewer as complete; all level assignments remain provisional until certified by an authorized reviewer.

**Definition 9: Journey Position.** The structured snapshot of a run's location in the journey map at a given moment, encoded as a JourneyPosition dataclass (journey_position.json) with fields [OBSERVED from schema.py]: run_id, raw_goal, north_star_relevance (one of: none, low, medium, high, direct), current_capability_level, likely_lanes (list), known_related_components (list), known_blockers (list), owner_dependent (boolean), can_advance_now (boolean), anti_loop_warning (optional), must_pick_concrete_slice (boolean). Produced by the position subcommand. This dataclass implements the 4-tuple (relevance, level, lanes, blockers) from Section 4.1: north_star_relevance maps to relevance, current_capability_level maps to level, likely_lanes maps to lanes, and known_blockers maps to blockers; the remaining seven fields (run_id, raw_goal, known_related_components, owner_dependent, can_advance_now, anti_loop_warning, must_pick_concrete_slice) are implementation-level extensions of those four abstract coordinates.

**Definition 10: Journey Map Update.** A structured record committing a completed run's outcome to the global map, produced by the update subcommand at the terminal JMT stage. Stored as journey_map_update.md (per-run narrative) and appended to journey_history.jsonl (the append-only global log). Also updates current_position.md, next_unlocks.json, and (when a milestone completes) appends to completed_milestones.jsonl. All writes are atomic (tmp + os.replace) [OBSERVED from artifacts.py].

These ten definitions exist because a practitioner who watches their pipeline loop without progress needs a vocabulary to name what went wrong: not "the agent failed," but specifically which gate was unmet, which lane was wrong, or which blocker was never named. The definitions are the shared vocabulary that turns that failure from opaque to diagnosable.

---

## 7. Pipeline Architecture

### 7.1 Overview

The sixteen-stage architecture below is the formal specification of how JMT interleaves into an existing pipeline. Stage counts are observable in cli.py. The reference implementation interleaves five JMT stages into an existing 11-stage host pipeline, producing a 16-stage architecture. All five JMT stages are gated by the feature flag QAH_GO_JOURNEY_MAP: when the flag is off, the pipeline is byte-for-byte unchanged [OBSERVED from the journey_required() function]. The grounding notes use a collapsed 14-stage view for brevity, combining some adjacent host and JMT stages; the full enumeration in Section 7.2 lists 16 distinct stages.

### 7.2 Stage-by-Stage Architecture

The 16-stage pipeline in order:

1. **Raw Signal Capture** (host). The latent_ambition hook captures the raw user input and writes 00_raw_signal.md.

2. **Journey Map Positioning [JMT].** CLI subcommand: `position`. Reads the raw goal, runs deterministic marker-matching, and writes journey_position.json. Fields: run_id, raw_goal, north_star_relevance, likely_lanes[], known_blockers[], can_advance_now. This stage answers: "where is this task in the journey map?" When north_star_relevance is none or low, the position artifact sets must_pick_concrete_slice=True. That flag directs the pipeline to ground the task in a concrete first slice before lane selection proceeds. This is the proposed mechanism by which North Star relevance steers agent behavior toward the declared system intent.

3. **Latent Ambition Compiler** (host). The latent_ambition module expands the raw signal into the deeper ambition behind the request and writes 01_latent_ambition.json.

4. **Journey Lane Selection [JMT].** CLI subcommand: `select-lane`. Reads the latent ambition and position. Selects the primary lane and milestone. Writes journey_lane.json. Fields: primary_lane, selected_milestone, target_gate, progress_type, why_this_lane, artifact_that_proves_progress, secondary_lanes[], what_not_to_repeat[]. This stage answers: "which lane, which milestone, and what artifact proves we got there?"

5. **Self-Prompt Compiler** (host, go_loop). Compiles the self-prompt that the agent will execute.

6. **Exploration Engine** (host, conditional). The exploration-discovery MCP server runs when the task is novel, ambiguous, or requires invention before planning.

7. **Prompt Tailor** (host, prompt-tailor MCP). Transforms the raw idea into a structured scaffold with filled slots.

8. **Planner** (host, prompt-tailor-planner). Expands the filled scaffold into a spec.md.

9. **Journey Gate Alignment [JMT].** CLI subcommand: `align-gate`. Reads the plan and lane selection. Aligns gate conditions to the planned artifacts. Writes journey_gate_alignment.json. Fields: lane, release_gate, success_condition, failure_condition, planned_artifacts[], required_tests[], qa_checks[], blocked_claims[]. This stage answers: "what exactly must the generator produce, and what must QA verify, for this gate to pass?"

10. **Generator** (host, prompt-tailor-generator). Produces the primary artifact.

11. **QA / Evaluator** (host, prompt-tailor-qa-evaluator). Evaluates the artifact and writes qa_report.md.

12. **Journey Progress Check [JMT].** CLI subcommand: `progress`. Reads the QA report, release context, and gate alignment. Evaluates whether at least one concrete progress signal is present. Writes journey_progress_check.json. Fields: lane, milestone, before_level, after_level, progress_made, progress_type, next_unlock, evidence[], blocker?, recommended_release. Exit code: 0 for progress_made=True; 1 for progress_made=False. This stage answers: "did this run actually advance the journey?"

13. **Release Gate** (host). Reads the release_verdict.json and decides whether to release.

14. **Journey Map Update [JMT].** CLI subcommand: `update`. Commits the run outcome to the global map. Writes journey_map_update.md (per-run narrative) and appends to journey_history.jsonl. Also updates current_position.md and next_unlocks.json. This stage answers: "what has permanently changed in the journey map as a result of this run?"

15. **Stop Gate** (host). The stop-requires-tailor-and-qa.py hook verifies required artifacts exist and release_verdict.json contains PASS or PASS_WITH_WARNINGS.

16. **Final Report** (host). Writes final_report.md.

See Figure 1 (standard pipeline without JMT) and Figure 2 (/go pipeline with JMT) below.

```
+-----------------------------+
| Raw Signal Capture |
| (latent_ambition hook) |
+-------------+---------------+
 |
 v
+-----------------------------+
| Latent Ambition Compiler |
| (latent_ambition module) |
+-------------+---------------+
 |
 v
+-----------------------------+
| Self-Prompt Compiler |
| (go_loop) |
+-------------+---------------+
 |
 v
+-----------------------------+
| Exploration Engine |
| (conditional, MCP) |
+-------------+---------------+
 |
 v
+-----------------------------+
| Prompt Tailor |
| (prompt-tailor MCP) |
+-------------+---------------+
 |
 v
+-----------------------------+
| Planner |
| (prompt-tailor-planner) |
+-------------+---------------+
 |
 v
+-----------------------------+
| Generator |
| (prompt-tailor-generator) |
+-------------+---------------+
 |
 v
+-----------------------------+
| QA / Evaluator |
| (prompt-tailor-qa-evaluator)|
+-------------+---------------+
 |
 v
+-----------------------------+
| Release Gate |
| (release_verdict.json) |
+-------------+---------------+
 |
 v
+-----------------------------+
| Stop Gate |
| (stop-requires-tailor-and- |
| qa.py hook) |
+-------------+---------------+
 |
 v
+-----------------------------+
| Final Report |
| (final_report.md) |
+-----------------------------+

 Journey position is IMPLICIT and LOST
 across pipeline runs. No persistent
 navigation state is maintained.
```

*Figure 1: Standard /go pipeline without Journey Map Thinking. Eleven host stages execute in sequence. No persistent navigation layer exists: which lane the agent is in, which milestone it targets, whether a gate has been met, and what blockers exist are all implicit and not recorded between runs.*

```
+-----------------------------+
| Raw Signal Capture |
| (latent_ambition hook) |
+-------------+---------------+
 |
 v
+=============================+ journey_position.json
| [JMT] Journey Map +-------> north_star_relevance,
| Positioning | likely_lanes[],
| (cli: position) | known_blockers[],
+=============================+ can_advance_now
 |
 v
+-----------------------------+
| Latent Ambition Compiler |
| (latent_ambition module) |
+-------------+---------------+
 |
 v
+=============================+ journey_lane.json
| [JMT] Journey Lane +-------> primary_lane,
| Selection | selected_milestone,
| (cli: select-lane) | target_gate,
+=============================+ what_not_to_repeat[]
 |
 v
+-----------------------------+
| Self-Prompt Compiler |
| (go_loop) |
+-------------+---------------+
 |
 v
+-----------------------------+
| Exploration Engine |
| (conditional, MCP) |
+-------------+---------------+
 |
 v
+-----------------------------+
| Prompt Tailor |
| (prompt-tailor MCP) |
+-------------+---------------+
 |
 v
+-----------------------------+
| Planner |
| (prompt-tailor-planner) |
+-------------+---------------+
 |
 v
+=============================+ journey_gate_alignment.json
| [JMT] Journey Gate +-------> success_condition,
| Alignment | planned_artifacts[],
| (cli: align-gate) | required_tests[],
+=============================+ blocked_claims[]
 |
 v
+-----------------------------+
| Generator |
| (prompt-tailor-generator) |
+-------------+---------------+
 |
 v
+-----------------------------+
| QA / Evaluator |
| (prompt-tailor-qa-evaluator)|
+-------------+---------------+
 |
 v
+=============================+ journey_progress_check.json
| [JMT] Journey Progress +-------> progress_made (bool),
| Check | progress_type,
| (cli: progress) | next_unlock,
+=============================+ recommended_release
 |
 v
+-----------------------------+
| Release Gate |
| (release_verdict.json) |
+-------------+---------------+
 |
 v
+=============================+ journey_map_update.md
| [JMT] Journey Map Update +-------> (per-run narrative)
| (cli: update) |
+=============================+ journey_history.jsonl
 | -------> (append-only global log)
 v
+-----------------------------+
| Stop Gate |
| (stop-requires-tailor-and- |
| qa.py hook) |
+-------------+---------------+
 |
 v
+-----------------------------+
| Final Report |
| (final_report.md) |
+-----------------------------+

 [JMT] = Journey Map Thinking stage
 Feature flag: QAH_GO_JOURNEY_MAP
 Off => pipeline is byte-for-byte unchanged
```

*Figure 2: /go pipeline with Journey Map Thinking active (QAH_GO_JOURNEY_MAP=1). Five JMT stages (marked [JMT]) interleave with the existing eleven host stages, which are unchanged. Each JMT stage runs a deterministic CLI subcommand and writes a typed artifact. When the feature flag is off, the pipeline reverts to the Figure 1 form with no modification to any host stage [OBSERVED: journey_required() reads QAH_GO_JOURNEY_MAP from the environment].*

---

## 8. Artifact Protocol

### 8.1 Overview

The seven artifacts produced by a JMT-active run form a closed, append-only record. No artifact is modified after it is written; all replacements use atomic tmp+os.replace [OBSERVED from artifacts.py]. The JMT artifact protocol produces seven typed files across a pipeline run. Five are per-run artifacts (written fresh each run by the five JMT stages). Two are global artifacts that persist across all runs and accumulate the journey's history [OBSERVED from artifacts.py and the seeded global map].

The global map root is `<repo>/.runs/journey_map/`. All writes are atomic: the implementation uses a temporary file followed by os.replace, which is an atomic operation on POSIX filesystems [OBSERVED from artifacts.py]. The two history files (journey_history.jsonl and completed_milestones.jsonl) are append-only: new lines are added but existing lines are never overwritten.

### 8.2 Per-Run Artifacts

**journey_position.json** (JMT Positioning stage). Fields: run_id, raw_goal, north_star_relevance, current_capability_level, likely_lanes[], known_related_components[], known_blockers[], owner_dependent, can_advance_now, anti_loop_warning (optional), must_pick_concrete_slice. Also carries honest_scope and scope_walls_certified.

**journey_lane.json** (JMT Lane Selection stage). Fields: primary_lane, selected_milestone, target_gate, progress_type, why_this_lane, artifact_that_proves_progress, secondary_lanes[], what_not_to_repeat[]. Also carries honest_scope and scope_walls_certified.

**journey_gate_alignment.json** (JMT Gate Alignment stage). Fields: lane, release_gate, success_condition, failure_condition, planned_artifacts[], required_tests[], qa_checks[], blocked_claims[]. Also carries honest_scope and scope_walls_certified.

**journey_progress_check.json** (JMT Progress Check stage). Fields: lane, milestone, before_level, after_level, progress_made, progress_type, next_unlock, evidence[], blocker (optional), recommended_release. Also carries honest_scope and scope_walls_certified.

**journey_map_update.md** (JMT Map Update stage). A human-readable narrative of the run's outcome and its effect on the global map.

### 8.3 Global Artifacts

**journey_history.jsonl** (global, append-only). One JSON object per completed pipeline run. Accumulated across all runs; never overwritten. The following is a real entry from the install run that built the JMT layer itself [OBSERVED, verbatim from the seeded global map]:

```json
{"run_id": "go_go_ultracode_run_install_journey_2026_06_13", "lane": "A", "milestone": "self-prompt compiler", "progress_made": true, "progress_type": "BUILD_ARTIFACT", "evidence": ["artifact_changed", "gate_passed", "test_added", "changed_files=1"], "blocker": null, "release_verdict": "PASS"}
```

**blocker_map.json** (global, atomic). A lane-keyed map of named blockers. Each entry carries a description, an owner_dependent boolean, and a next_unlock string. Real contents (abbreviated) [OBSERVED from the seeded global map]:

- Lane F: "no trained specialist checkpoint on disk for some specialists" (owner_dependent=False).
- Lane I: "earlyoom.service inactive; owner action required" (owner_dependent=True, next_unlock: "owner enables earlyoom / approves resident service").
- Lane M: "owner opt-in + production approval required" (owner_dependent=True).

### 8.4 Honest-Scope Footer

Every artifact carries two fields that prevent overclaim propagation [OBSERVED from schema.py dataclasses]:

```
honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
scope_walls_certified: false
```

This is a structural mechanism, not a disclaimer. A downstream consumer of any JMT artifact that reads these fields knows not to treat the artifact as a certified result.

The seven artifacts described in this section are the concrete answer to the handoff-failure scenario from Section 2: when the next run opens, it reads journey_position.json and journey_lane.json instead of reconstructing context from raw prose history, and the honest-scope footer prevents any artifact from silently carrying forward a false progress claim into that reconstruction.

### 8.5 Artifact Protocol Lifecycle

See Figure 4 for the full lifecycle diagram.

```
PER-RUN ARTIFACTS (written fresh each pipeline run, atomic tmp+os.replace):

 [JMT: position] [JMT: select-lane]
 | |
 v v
+-----------------+ +------------------+
| journey_ | | journey_ |
| position.json | | lane.json |
| | | |
| run_id | | primary_lane |
| raw_goal | | selected_ |
| north_star_ | | milestone |
| relevance | | target_gate |
| likely_lanes[] | | progress_type |
| known_blockers[]| | artifact_that_ |
| can_advance_now | | proves_ |
| honest_scope: | | progress |
| PROVISIONAL.. | | what_not_to_ |
+-----------------+ | repeat[] |
 | | honest_scope: |
 | | PROVISIONAL.. |
 | +------------------+
 | |
 +----------+--------------+
 |
 v
 +------------------+
 | journey_gate_ | [JMT: align-gate]
 | alignment.json |
 | |
 | lane |
 | release_gate |
 | success_ |
 | condition |
 | planned_ |
 | artifacts[] |
 | required_tests[] |
 | qa_checks[] |
 | blocked_claims[] |
 | honest_scope: |
 | PROVISIONAL.. |
 +--------+---------+
 |
 [build + QA run]
 |
 v
 +------------------+
 | journey_ | [JMT: progress]
 | progress_check |
 |.json |
 | |
 | progress_made |
 | progress_type |
 | next_unlock |
 | recommended_ |
 | release |
 | honest_scope: |
 | PROVISIONAL.. |
 +--------+---------+
 |
 v
 +------------------+
 | journey_map_ | [JMT: update]
 | update.md |
 | (per-run narr.) |
 +--------+---------+
 |
 +--------+---------+
 | |
 v v
GLOBAL ARTIFACTS (persist across all runs):

+----------------------+ +----------------------+
| journey_history. | | blocker_map.json |
| jsonl | | |
| (APPEND-ONLY) | | atomic os.replace |
+----------------------+ +----------------------+

All artifacts carry:
 honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE
 scope_walls_certified: false
```

*Figure 4: JMT artifact protocol lifecycle. Per-run artifacts are written by each of the five JMT stages. Global artifacts are written atomically (blocker_map.json via tmp+os.replace) or appended to (journey_history.jsonl). All artifacts carry an honest-scope footer [OBSERVED from artifacts.py]. The lifecycle above is the direct answer to the handoff-failure scenario from Section 2: a run that opens journey_position.json and journey_lane.json instead of reconstructing context from raw prose never faces the blank context window that costs the practitioner their full next budget.*

---

## 9. Implementation Pattern: 2,017 Lines, Zero LLM Calls, Five Subcommands

### 9.1 File Structure

The reference implementation consists of eleven Python files totaling approximately 2,017 lines [OBSERVED from the source at quark-studio/src/qai_core/qah/journey_map/]. Nine modules implement the five-stage navigation layer (approximately 1,413 lines); the package also carries a package-init re-export module and a separate forward-simulation module:

| File | LOC | Role |
|------|-----|------|
| schema.py | 234 | Dataclasses (JourneyPosition, JourneyLaneSelection, JourneyGateAlignment, JourneyProgressCheck), NORTH_STAR constant, CAPABILITY_LEVELS, PROGRESS_TYPES, RELEVANCE |
| lanes.py | 254 | The 14 journey lane definitions with marker vocabularies and MATCH_PRIORITY |
| position.py | 134 | Deterministic positioner: marker-matching, relevance scoring, anti-loop detection |
| selector.py | 147 | Lane and milestone selector: owner-dependent packet emission, what_not_to_repeat |
| gate_alignment.py | 72 | Gate alignment: maps planned artifacts and tests to gate conditions |
| progress.py | 86 | Progress check: concrete-signal detection, no-progress guard |
| update.py | 98 | Map update: commits outcome to global map, appends to history |
| artifacts.py | 155 | Artifact I/O: atomic writes (tmp + os.replace), append-only history |
| cli.py | 233 | CLI: 5 subcommands (position, select-lane, align-gate, progress, update) plus seed |
| __init__.py | 85 | Package exports: re-exports the five stage functions, the lane catalog, the schema dataclasses, and the vocabulary constants |
| forward_journey.py | 519 | Deterministic forward-simulation module: computes an ordered milestone path from a measured current state toward the declared North Star, with a verdict function gated on benchmark evidence. Makes no LLM calls. This module is auxiliary to the five-stage layer and is not invoked by the five CLI subcommands |

The per-file counts sum to the toolchain-verified total of 2,017 lines across 11 files (the nine-module five-stage subtotal is 1,413 lines), matching the wc -l measurement that was independently reproduced by a second, non-Claude toolchain [OBSERVED].

No LLM calls exist anywhere in the JMT layer. All routing, positioning, and progress evaluation are deterministic marker-matching and boolean-signal detection.

### 9.2 CLI Invocation Order

The five JMT subcommands are invoked in the following order within a pipeline run:

```bash
# Stage [0.25]: After raw signal capture
python -m qai_core.qah.journey_map.cli position \
 --raw "$RAW_GOAL" \
 --run-id "$RUN_ID" \
 --output journey_position.json

# Stage [1.25]: After latent ambition compilation
python -m qai_core.qah.journey_map.cli select-lane \
 --position journey_position.json \
 --ambition "$LATENT_AMBITION" \
 --output journey_lane.json

# Stage [4.5]: After planner
python -m qai_core.qah.journey_map.cli align-gate \
 --lane journey_lane.json \
 --spec spec.md \
 --output journey_gate_alignment.json

# Stage [7]: After QA/Evaluator
python -m qai_core.qah.journey_map.cli progress \
 --gate journey_gate_alignment.json \
 --qa-report qa_report.md \
 --release-verdict release_verdict.json \
 --output journey_progress_check.json
# Exit code 0 = progress_made=True; exit code 1 = progress_made=False

# Stage [8.5]: After Release Gate
python -m qai_core.qah.journey_map.cli update \
 --progress journey_progress_check.json \
 --lane journey_lane.json \
 --map-root.runs/journey_map/ \
 --output journey_map_update.md
```

The seed command initializes the global map:

```bash
python -m qai_core.qah.journey_map.cli seed \
 --map-root.runs/journey_map/
```

### 9.3 Exit Code Contract

The CLI exit codes are [OBSERVED from cli.py]:

| Code | Meaning | Stage |
|------|---------|-------|
| 0 | OK (or progress_made=True for progress subcommand) | all |
| 1 | No progress (progress_made=False) | progress only |
| 2 | Error (invalid input, missing file, etc.) | all |
| 3 | Usage error (wrong arguments) | all |

The exit code 1 from the progress subcommand is wired to the pipeline host's conditional logic: a non-zero exit from the progress check triggers the BLOCKED_NO_PROGRESS path.

### 9.4 No-Progress Guard

The progress check enforces an anti-vagueness rule [OBSERVED from progress.py]: progress_made is set to True if and only if at least one of the following concrete signals is present:

- A changed file (any file in the run directory was created or modified).
- A passed gate (the release verdict is PASS or PASS_WITH_WARNINGS, or the QA verdict starts with "PASS").
- A test was added (evidence of new test coverage).
- A benchmark was run.
- A model was changed (checkpoint modified).
- A dogfood run was completed.
- An owner-unlock packet was produced.

When none of these signals is present, the output is forced to:

```
progress_made: false
progress_type: BLOCKED_NO_SAFE_ACTION
recommended_release: BLOCKED_NO_PROGRESS
next_unlock: "produce a concrete artifact or report a true blocker; never record a summary"
```

This is the mechanism that prevents the "prose-summary progress claim" failure mode (Section 4.3(c)).

### 9.5 Dataclass Validator Contract

Each of the four JMT dataclasses (JourneyPosition, JourneyLaneSelection, JourneyGateAlignment, JourneyProgressCheck) carries a validate() method that returns a list of error strings [OBSERVED from schema.py]. An empty list means the artifact is internally consistent; a non-empty list causes the CLI to emit errors and exit with code 2.

The implementation pattern described in this section solves a concrete engineering problem: a practitioner hand-off that begins with a run claiming progress and ends with the next run spending its full budget reconstructing what was actually done. The eleven files, five subcommands, and seven artifacts are the mechanism that prevents that reconstruction cost, by writing a durable, typed record of position and progress at the close of every run.

---

## 10. Algorithm: Formal Specification

<!-- honest_scope: PROVISIONAL_PAPER_DRAFT_NO_OUTPUT_QUALITY_GUARANTEE -->
<!-- scope_walls_certified: false -->

**Practitioner fast-path.** For orientation, read Sections 5 and 9 first. For a specific routing branch, go to the decision tables at Section 10.8. Return to 10.2 through 10.7 for the full pseudocode of each subcommand.

**Reader orientation.** This section is a reference specification for the five deterministic CLI subcommands. The pseudocode in 10.3 through 10.7 maps one-to-one to a source file and a set of decision tables (10.8); no step is invented.

**Framing.** The pseudocode below formalizes the existing deterministic code. Every step is annotated with its source file and line number; no rule is invented. A reader who doubts any step can inspect the cited file directly.

The algorithm comprises one top-level driver (JOURNEY-MAP) and five sub-algorithms, followed by six decision tables.

### 10.1 Data Summary

Key constants [OBSERVED from source files listed in Section 9.1]:

| Constant | Value | Source |
|---|---|---|
| NORTH_STAR | "QAH as an Ambition-to-Reality Operating System" | schema.py:16 |
| RELEVANCE | ("none", "low", "medium", "high", "direct") | schema.py:23 |
| CAPABILITY_LEVELS | 11 members, L0_CONCEPT through L10_AMBITION_TO_REALITY_OS | schema.py:25-37 |
| PROGRESS_TYPES | 14 members, BUILD_ARTIFACT through BLOCKED_NO_SAFE_ACTION | schema.py:39-54 |
| MATCH_PRIORITY | ("I","F","A","E","G","C","K","J","L","M","H","B","N","D") | lanes.py:224 |
| CLI exit codes | 0=ok, 1=no-progress, 2=error, 3=usage | cli.py:21-22 |
| Global files seeded | north_star.json, journey_lanes.json, component_levels.json, blocker_map.json, completed_milestones.jsonl, journey_history.jsonl, next_unlocks.json, current_position.md | artifacts.py:25-34 |

### 10.2 JOURNEY-MAP Driver

**Source:** cli.py:main (line 219), cli.py:\_cmd\_position through \_cmd\_update

```
JOURNEY-MAP(raw_goal, run_id, component_levels):

 -- Feature-flag check. [artifacts.py:journey_required, lines 37-40]
 -- Reads environment variable QAH_GO_JOURNEY_MAP.
 -- Truthy values: "1", "true", "yes", "on" (case-insensitive).
 IF NOT journey_required():
 RETURN (pipeline skipped; feature flag is off; host pipeline is unchanged)

 -- Stage 1: locate the task on the map.
 -- [cli.py:_cmd_position, line 86; position.py:position, line 63]
 pos <- POSITION(raw_goal, run_id, component_levels)

 -- Stage 2: choose the lane and milestone.
 -- [cli.py:_cmd_select_lane, line 96; selector.py:select_lane, line 42]
 sel <- SELECT-LANE(pos, ambition?)

 -- Stage 3: align gate conditions for the Planner.
 -- [cli.py:_cmd_align_gate, line 108; gate_alignment.py:align_gate, line 25]
 gate_aln <- ALIGN-GATE(sel, spec_text?)

 -- Stage 4: evaluate whether real progress occurred.
 -- [cli.py:_cmd_progress, line 117; progress.py:check_progress, line 22]
 chk <- CHECK-PROGRESS(sel,
 changed_files, tests_added, gate_passed, benchmark_ran,
 model_changed, dogfood_ran, unlock_packet,
 qa_verdict, release_verdict,
 before_level, after_level, milestone?)

 -- Stage 5: persist the run outcome to the global map.
 -- [cli.py:_cmd_update, line 145; update.py:update_map, line 17]
 md <- UPDATE-MAP(chk, sel, global_root, run_id, release_verdict?)

 RETURN (pos, sel, gate_aln, chk, md)
```

The five stages are strictly linear: each stage reads the output of the previous stage. No stage makes an LLM call. All routing is marker-matching and boolean-signal detection.

### 10.3 POSITION

**Source:** position.py:position (lines 63-134)

```
POSITION(raw_goal, run_id, component_levels):

 -- P1: text normalization. [position.py:70]
 text <- raw_goal.lower().strip()
 levels <- component_levels OR {}

 -- P2: vision detection (highest-priority flag). [position.py:73; lanes.py:is_vision, line 253] -- matches VISION_MARKERS (7 strings; see Marker Reference, Section 10.8). Vision=True suppresses trivial and status_only (P3, P4).
 vision <- is_vision(text)

 -- P3: trivial detection (suppressed when vision=True). [position.py:74] -- _is_trivial [position.py:51-54]: true on a TRIVIAL_MARKERS hit (24 strings; see Section 10.8) OR a _TRIVIAL_EXTRA token.
 trivial <- _is_trivial(text) AND NOT vision

 -- P4: status-only detection (suppressed when vision=True). [position.py:57-60, 75; token lists in Table G, 10.8]
 status_only <- _is_status_only(text) AND NOT vision

 -- P5: lane matching (MATCH_PRIORITY order). [position.py:76; lanes.py:246-250]
 -- matched_lanes: filters MATCH_PRIORITY by marker substring hit.
 -- Result preserves MATCH_PRIORITY order; matched[0] is highest-priority.
 matched <- matched_lanes(text)

 -- P6: moonshot signal; classify_request(raw_goal) returns (moonshot_bool, exploration_bool); second value discarded here. [latent_ambition/compiler.py:154-170; position.py:77]
 should_moonshot, _ <- classify_request(raw_goal)

 -- P7: anti-loop warning (set only when status_only=True). [position.py:79-84]
 anti_loop_warning <- None
 IF status_only:
 anti_loop_warning <-
 "status-only request: no lane is advanced by repeating a summary; "
 "pick a concrete artifact to produce or report a true blocker"

 -- P8: relevance ladder (4 branches, first match wins). [position.py:87-95]
 -- _CORE_LANES = {"A","C","D","F","G","I","J","K","L","M"} [position.py:21].
 IF vision:
 relevance <- "direct"
 ELIF status_only OR trivial:
 relevance <- "low"
 ELIF matched is non-empty:
 is_core <- any(lid in _CORE_LANES for lid in matched)
 IF should_moonshot OR is_core:
 relevance <- "high"
 ELSE:
 relevance <- "medium"
 ELSE:
 relevance <- "low"

 -- P9: capability level and aggregate fields. [position.py:98-118]
 capability_level <- "NA_TRIVIAL_OR_UNMAPPED"
 likely_lanes <- []
 components <- []
 blockers <- []
 owner_dependent <- False

 IF vision:
 -- VISION_LANE = "North-Star / Vision-to-Execution" [schema.py:19].
 likely_lanes <- [VISION_LANE]
 capability_level <- "L10_AMBITION_TO_REALITY_OS"
 ELIF matched is non-empty:
 likely_lanes <- list(matched)
 top <- get_lane(matched[0]) -- [lanes.py:get_lane, line 242]
 IF top is not None:
 capability_level <- levels.get(top.component, top.provisional_level)
 FOR lid IN matched:
 lane <- get_lane(lid)
 IF lane is not None:
 components.append(lane.component)
 blockers.extend(lane.blockers)
 owner_dependent <- owner_dependent OR lane.owner_dependent

 -- P10: can_advance_now (simple two-predicate conjunction). [position.py:120]
 can_advance_now <- (NOT owner_dependent) AND (NOT status_only)

 -- P11: return JourneyPosition dataclass. [position.py:122-134; schema.py]
 RETURN JourneyPosition(
 run_id = run_id OR "journey_position",
 raw_goal = raw_goal,
 north_star_relevance = relevance,
 current_capability_level = capability_level,
 likely_lanes = likely_lanes,
 known_related_components = components,
 known_blockers = blockers,
 owner_dependent = owner_dependent,
 can_advance_now = can_advance_now,
 anti_loop_warning = anti_loop_warning,
 must_pick_concrete_slice = vision,
 )
```

### 10.4 SELECT-LANE

**Source:** selector.py:select\_lane (lines 42-142)

```
SELECT-LANE(position, ambition?):

 text <- position.raw_goal.lower() -- [selector.py:47]
 matched <- list(position.likely_lanes) -- [selector.py:48]

 -- Four special cases, evaluated top-to-bottom; first match returns immediately.
 -- Fall-through to the normal path if none fires.

 -- Case 1: pure-vision ask. [selector.py:51-64]
 IF position.must_pick_concrete_slice:
 RETURN JourneyLaneSelection(
 primary_lane = VISION_LANE,
 selected_milestone = "choose and spec ONE concrete, buildable first slice",
 target_gate = "a concrete first slice is selected and routed to a real lane (A-N)",
 progress_type = "BUILD_ARTIFACT",
 why_this_lane = "pure-vision ask; the only honest move is to pick a concrete first slice",
 artifact_that_proves_progress = "first_slice_spec.md naming one real lane task",
 secondary_lanes = [],
 what_not_to_repeat = [
 "restating the vision without a concrete slice",
 "claiming a North Star milestone is reached",
 ],
 )

 -- Case 2: status-only / anti-loop. [selector.py:66-77]
 IF position.anti_loop_warning is not None:
 RETURN JourneyLaneSelection(
 primary_lane = "ordinary/blocked",
 selected_milestone = "choose a concrete artifact or report a true blocker",
 target_gate = "a concrete artifact is chosen, or a true blocker is reported",
 progress_type = "BLOCKED_NO_SAFE_ACTION",
 why_this_lane = "status-only request advances no lane; refuse to manufacture progress",
 artifact_that_proves_progress = "a concrete chosen artifact (none yet)",
 what_not_to_repeat = ["repeating the readiness summary"],
 )

 -- Case 3: owner-dependent blocker. [selector.py:81-108]
 -- Emits an owner-unlock packet; continues owner-independent work in parallel.
 IF position.owner_dependent AND matched is non-empty:
 primary <- matched[0]
 lane <- get_lane(primary)
 owner_independent <- [lid for lid in matched if NOT _owner_dependent(lid)]
 milestone <- lane.milestones[0] IF lane AND lane.milestones ELSE "owner opt-in packet"
 gate <- lane.gates[0] IF lane AND lane.gates ELSE "owner reviews + approves"
 domain_artifact <- lane.progress_artifacts[0] IF lane AND lane.progress_artifacts ELSE "a release verdict"
 boundary <- lane.claim_boundary IF lane ELSE "do not overclaim"
 RETURN JourneyLaneSelection(
 primary_lane = primary,
 selected_milestone = milestone,
 target_gate = gate,
 progress_type = "CREATE_OWNER_PACKET",
 why_this_lane = "lane {primary} is owner-dependent; produce unlock packet, continue owner-independent work in parallel",
 artifact_that_proves_progress = "owner_opt_in_packet.md + owner-independent {domain_artifact}",
 secondary_lanes = owner_independent OR ["D"],
 what_not_to_repeat = ["claiming production-ready before owner approval", boundary],
 )

 -- Case 4: trivial or unmapped (matched is empty). [selector.py:110-120]
 IF matched is empty:
 RETURN JourneyLaneSelection(
 primary_lane = "ordinary/maintenance",
 selected_milestone = "complete the small task and read it back",
 target_gate = "the small task is done and a read-back confirms it",
 progress_type = "FIX_DEFECT",
 why_this_lane = "trivial task; not on a journey lane and not inflated into one",
 artifact_that_proves_progress = "the edited file (read-back confirmed)",
 what_not_to_repeat = ["inflating a trivial task into a moonshot"],
 )

 -- Normal path (all four special cases failed to match). [selector.py:122-142]

 -- C-lane metric-target override: fires when lane C is matched AND raw_goal
 -- contains a digit-percent or digit-x pattern [selector.py:38-39].
 IF "C" in matched AND _has_metric_target(text):
 primary <- "C"
 ELSE:
 primary <- matched[0]

 secondary <- [lid for lid in matched if lid!= primary][:3]
 lane <- get_lane(primary)
 milestone <- lane.milestones[0] IF lane.milestones ELSE "advance {lane.name}"
 target_gate <- lane.gates[0] IF lane.gates ELSE "independent QA + release verdict"
 artifact <- lane.progress_artifacts[0] IF lane.progress_artifacts ELSE "a release verdict"
 why <- "markers route to lane {primary} ({lane.name}); moves closest to the North Star"
 IF ambition AND ambition.get("ambition_archetype"):
 why <- why + "; latent archetype {ambition['ambition_archetype']}"

 -- Lane-to-progress-type lookup (Table C). [selector.py:20-35, 137]
 progress_type <- _LANE_PROGRESS.get(primary, "BUILD_ARTIFACT")

 RETURN JourneyLaneSelection(
 primary_lane = primary,
 selected_milestone = milestone,
 target_gate = target_gate,
 progress_type = progress_type,
 why_this_lane = why,
 artifact_that_proves_progress = artifact,
 secondary_lanes = secondary,
 what_not_to_repeat = [
 lane.claim_boundary OR "do not overclaim",
 "do not restate readiness",
 ],
 )
```

### 10.5 ALIGN-GATE

**Source:** gate\_alignment.py:align\_gate (lines 25-72)

```
ALIGN-GATE(selection, spec_text?):

 lane_id <- selection.primary_lane -- [gate_alignment.py:31]
 lane <- get_lane(lane_id) -- [gate_alignment.py:32]

 -- AG1: initialize lists with sentinel values. [gate_alignment.py:34-37]
 -- _GLOBAL_BLOCKED_CLAIMS (2 strings, gate_alignment.py:19-22): North-Star gate
 -- and no-vague-progress rules; see Table F for build-test lane set.
 planned_artifacts <- [selection.artifact_that_proves_progress]
 qa_checks <- ["QA inspects the ACTUAL built artifact, not the spec or intent"]
 blocked_claims <- list(_GLOBAL_BLOCKED_CLAIMS)
 required_tests <- []

 -- AG2: extend from catalog lane if found. [gate_alignment.py:39-51]
 IF lane is not None:
 planned_artifacts <- list(dict.fromkeys(
 lane.progress_artifacts + planned_artifacts
 ))
 qa_checks <- lane.gates + qa_checks
 IF lane.claim_boundary:
 blocked_claims.append(lane.claim_boundary)
 IF lane_id IN {"A","B","D","H","I","J","L","N"}:
 required_tests <- [
 "uv run ruff check <changed>",
 "uv run mypy <changed>",
 "uv run pytest <related>",
 ]
 ELSE:
 required_tests <- [lane.gates[0] IF lane.gates ELSE "lane gate measurement"]
 ELSE:
 required_tests <- ["a read-back or a single relevant check"]

 -- AG3: compute release gate and condition strings. [gate_alignment.py:53-61]
 release_gate <- selection.target_gate
 success_condition <- (
 "the milestone '{selection.selected_milestone}' is met and "
 "'{selection.artifact_that_proves_progress}' exists with passing checks"
 )
 failure_condition <- (
 "no artifact produced or the gate did not pass -> BLOCKED_NO_PROGRESS / "
 "FAIL_REQUIRES_PATCH; never record fake progress"
 )

 RETURN JourneyGateAlignment(
 lane = lane_id,
 release_gate = release_gate,
 success_condition = success_condition,
 failure_condition = failure_condition,
 planned_artifacts = planned_artifacts,
 required_tests = required_tests,
 qa_checks = qa_checks,
 blocked_claims = blocked_claims,
 )
```

### 10.6 CHECK-PROGRESS

**Source:** progress.py:check\_progress (lines 22-86)

```
CHECK-PROGRESS(selection, changed_files, tests_added, gate_passed,
 benchmark_ran, model_changed, dogfood_ran, unlock_packet,
 qa_verdict, release_verdict, before_level, after_level,
 milestone?):

 files <- list(changed_files OR []) -- [progress.py:39]

 -- CP1: gate-pass disjunction (any one of 3 clauses suffices). [progress.py:40-44]
 -- _PASSING = ("PASS", "PASS_WITH_WARNINGS") [progress.py:19].
 gate <- (
 gate_passed
 OR release_verdict.upper() IN {"PASS", "PASS_WITH_WARNINGS"}
 OR qa_verdict.upper().startswith("PASS")
 )

 -- CP2: seven progress signals (boolean dict). [progress.py:46-53]
 -- Full signal names and source expressions: Table D (Section 10.8).
 signals <- {
 "artifact_changed": bool(files),
 "gate_passed": gate,
 "test_added": tests_added,
 "benchmark_ran": benchmark_ran,
 "model_changed": model_changed,
 "dogfood_ran": dogfood_ran,
 "unlock_packet": unlock_packet,
 }
 evidence <- [name for name, on in signals.items() if on]
 IF files:
 evidence.append("changed_files={len(files)}")

 -- CP3: progress_made = any() over all seven signals. [progress.py:58]
 -- Guard against silent looping: unless at least one signal fires,
 -- the run cannot record progress regardless of what prose it produced.
 progress_made <- any(signals.values())

 -- CP4: progress-type and blocker assignment. [progress.py:60-73]
 IF progress_made:
 progress_type <- selection.progress_type
 -- Unlock-packet override: fires only when gate did NOT pass. [progress.py:62-63]
 IF unlock_packet AND NOT gate:
 progress_type <- "CREATE_OWNER_PACKET"
 blocker <- None
 recommended <- ""
 next_unlock <- "advance {selection.primary_lane} toward {selection.target_gate}"
 ELSE:
 progress_type <- "BLOCKED_NO_SAFE_ACTION"
 blocker <- (
 "no_progress: no artifact, gate, test, benchmark, model, dogfood, or unlock packet"
 )
 recommended <- "BLOCKED_NO_PROGRESS"
 next_unlock <- (
 "produce a concrete artifact or report a true blocker; never record a summary"
 )

 RETURN JourneyProgressCheck(
 lane = selection.primary_lane,
 milestone = milestone OR selection.selected_milestone,
 before_level = before_level,
 after_level = after_level,
 progress_made = progress_made,
 progress_type = progress_type,
 next_unlock = next_unlock,
 evidence = evidence,
 blocker = blocker,
 recommended_release = recommended,
 )
```

### 10.7 UPDATE-MAP

**Source:** update.py:update\_map (lines 17-61); artifacts.py I/O helpers

```
UPDATE-MAP(progress, selection, global_root, run_id, release_verdict?):

 base <- Path(global_root)
 base.mkdir(parents=True, exist_ok=True) -- [update.py:27]

 -- UM1: append journey history (unconditional on every run). [update.py:29-39]
 -- append_jsonl [artifacts.py:65-69]: opens in append mode, writes one JSON line.
 history_entry <- {
 "run_id": run_id OR "journey_update",
 "lane": progress.lane,
 "milestone": progress.milestone,
 "progress_made": progress.progress_made,
 "progress_type": progress.progress_type,
 "evidence": progress.evidence,
 "blocker": progress.blocker,
 "release_verdict": release_verdict,
 }
 append_jsonl(base / "journey_history.jsonl", history_entry)

 -- UM2: append completed milestones (only when progress_made=True). [update.py:41-47]
 IF progress.progress_made:
 append_jsonl(base / "completed_milestones.jsonl", {
 "run_id": run_id OR "journey_update",
 "lane": progress.lane,
 "milestone": progress.milestone,
 "progress_type": progress.progress_type,
 })

 -- UM3: update next_unlocks.json (atomic replace every run). [update.py:49-57]
 -- write_json: mkstemp -> write -> os.replace (atomic on POSIX) [artifacts.py:43-50].
 next_path <- base / "next_unlocks.json"
 IF next_path.exists():
 data <- read_json(next_path)
 unlocks <- data.get("next_unlocks", {}) IF isinstance(data, dict) ELSE {}
 ELSE:
 unlocks <- {}
 unlocks[progress.lane] <- progress.next_unlock
 write_json(next_path, {"next_unlocks": unlocks, "honest_scope": HONEST_SCOPE})

 -- UM4: write current_position.md (unconditional on every run). [update.py:59-60]
 md <- render_update_md(progress, selection,
 run_id=run_id, release_verdict=release_verdict)
 (base / "current_position.md").write_text(md, encoding="utf-8")

 RETURN md
```

### 10.8 Decision Tables

**Table A: MATCH\_PRIORITY Precedence**

Source: lanes.py:224. The 14 lane IDs are evaluated in this order during matched\_lanes. A more specific lane (rank 1) outranks a generic lane (rank 14).

| Rank | Lane | Name | Representative Markers |
|------|------|------|------------------------|
| 1 | I | System Guardian Product | "linux", "daemon", "resident", "guardian", "always on" |
| 2 | F | Specialist Model Foundry | "from scratch", "fine-tune", "foundry", "specialist model" |
| 3 | A | Recursive /go Prompt Loop | "/go", "prompt loop", "recursive", "self-prompt" |
| 4 | E | Agent Run Reviewer | "agent run", "run reviewer", "what to do next" |
| 5 | G | Claim-Audit / truth\_auditor | "claim audit", "truth auditor", "readiness", "findings" |
| 6 | C | Goal-to-Gate Compiler | "metric", "percent", "target", "reduce", "increase" |
| 7 | K | Benchmark / Model Comparisons | "benchmark", "comparison", "leaderboard" |
| 8 | J | Open-World Runtime | "open world", "runtime", "benchmark inputs" |
| 9 | L | Quantum Research Track | "quantum", "pennylane", "born kernel" |
| 10 | M | Production Activation | "production", "deploy", "activate", "rollback" |
| 11 | H | Generated-Prose Specialist | "prose", "article", "essay", "blog post" |
| 12 | B | Latent Ambition Compiler | "latent ambition", "archetype", "ambition compiler" |
| 13 | N | Reflection / Memory | "reflection", "memory", "lesson learned" |
| 14 | D | Real Project Execution | "build a", "project", "scaffold", "app", "tool" |

[OBSERVED from lanes.py:224, lanes.py:53-217]

**Table B: Relevance Ladder**

Source: position.py:87-95. Branches evaluated top to bottom; first matching branch wins. \_CORE\_LANES = {"A","C","D","F","G","I","J","K","L","M"} [position.py:21].

| Priority | Condition | Assigned relevance |
|----------|-----------|-------------------|
| 1 | vision = True | "direct" |
| 2 | status\_only = True OR trivial = True | "low" |
| 3 | matched non-empty AND (should\_moonshot OR any matched lane in \_CORE\_LANES) | "high" |
| 4 | matched non-empty AND none of the above conditions hold | "medium" |
| 5 | matched is empty, not vision, not trivial, not status\_only | "low" |

[OBSERVED from position.py:87-95]

**Table C: Lane-to-Progress-Type Map**

Source: selector.py:20-35. Default when no catalog lane is found: BUILD\_ARTIFACT [selector.py:137].

| Lane | Progress Type |
|------|--------------|
| A | BUILD\_ARTIFACT |
| B | BUILD\_ARTIFACT |
| C | PASS\_GATE |
| D | BUILD\_ARTIFACT |
| E | QA\_VERIFY |
| F | TRAIN\_MODEL |
| G | PASS\_GATE |
| H | BUILD\_ARTIFACT |
| I | BUILD\_ARTIFACT |
| J | RUN\_BENCHMARK |
| K | RUN\_BENCHMARK |
| L | BUILD\_ARTIFACT |
| M | CREATE\_OWNER\_PACKET |
| N | REFLECT\_LESSON |

[OBSERVED from selector.py:20-35]

**Table D: Seven Progress Signals**

Source: progress.py:46-53. progress\_made = any(signals.values()) [progress.py:58]: a single True value is sufficient.

| Signal Name | Source expression |
|-------------|------------------|
| artifact\_changed | bool(files) where files = list(changed\_files or []) |
| gate\_passed | gate-pass disjunction (see Table E) |
| test\_added | tests\_added parameter (boolean) |
| benchmark\_ran | benchmark\_ran parameter (boolean) |
| model\_changed | model\_changed parameter (boolean) |
| dogfood\_ran | dogfood\_ran parameter (boolean) |
| unlock\_packet | unlock\_packet parameter (boolean) |

[OBSERVED from progress.py:46-58]

**Table E: Gate-Pass Disjunction**

Source: progress.py:40-44. Three clauses combined with OR; any one clause being true makes the gate pass. \_PASSING = ("PASS", "PASS\_WITH\_WARNINGS") [progress.py:19].

| Clause | Expression |
|--------|-----------|
| 1 | gate\_passed (boolean parameter passed directly to CHECK-PROGRESS) |
| 2 | release\_verdict.upper() in ("PASS", "PASS\_WITH\_WARNINGS") |
| 3 | qa\_verdict.upper().startswith("PASS") |

[OBSERVED from progress.py:40-44]

**Table F: Build-Test Lane Set**

Source: gate\_alignment.py:17, 45-51.

| Category | Lane IDs | Required tests |
|----------|----------|----------------|
| Build-test lanes | A, B, D, H, I, J, L, N | uv run ruff check, uv run mypy, uv run pytest |
| Gate-only catalog lanes | C, E, F, G, K, M | lane.gates[0] or "lane gate measurement" |
| No catalog lane | n/a | "a read-back or a single relevant check" |

[OBSERVED from gate\_alignment.py:17, 45-51]

**Table G: Status-Detection Token Lists**

Source: position.py:24-41. \_is\_status\_only returns True when any \_STATUS\_MARKERS token matches AND no \_WORK\_VERBS token matches.

| List | Token count | Representative tokens | Source lines |
|------|-------------|----------------------|--------------|
| \_STATUS\_MARKERS | 9 | "what's the status", "how are we doing", "any update", "progress so far" | position.py:24-34 |
| \_WORK\_VERBS | 15 | "build", "implement", "write", "create", "fix", "refactor", "add", "deploy" | position.py:37-41 |

[OBSERVED from position.py:24-41]

**Table H: Marker Reference**

Full string lists for the two inline classifiers used in POSITION (P2, P3). Sources are the authoritative file and line ranges; these lists are reproduced here so the pseudocode comments can stay on one line. [OBSERVED from lanes.py:227-235; latent_ambition/compiler.py:74-101]

| Classifier | Count | Full string list | Source |
|-----------|-------|-----------------|--------|
| VISION\_MARKERS | 7 | "push humanity forward", "change the world", "make history", "reshape", "revolutionary", "unprecedented", "transform humanity" | lanes.py:227-235 |
| TRIVIAL\_MARKERS | 24 | "hello", "hi", "hey", "what time", "what day", "tell me a joke", "joke", "what is the weather", "weather", "good morning", "good afternoon", "good evening", "good night", "thanks", "thank you", "ok", "okay", "sure", "yes", "no", "bye", "goodbye", "see you", "later" | latent\_ambition/compiler.py:74-101 |

[OBSERVED from lanes.py:227-235; latent_ambition/compiler.py:74-101]

---

## 11. Case Study: /go Pipeline

### 11.1 Negative Finding First: Positioner Failure on This Task (OBSERVED)

Before describing the run that succeeded, we report the run that failed the positioner. The JMT positioner was run on the task of writing this paper. The observed output was [OBSERVED from live CLI run]:

```
$ python -m qai_core.qah.journey_map.cli position --raw <this task> --output journey_position.json
OK: relevance=low lanes=[] owner_dependent=False anti_loop=False
```

This is a genuine failure of the positioner. The task of writing a research paper about the JMT system is a substantial, consequential task. The positioner returned relevance=low and an empty lane list because the marker vocabulary does not include "research paper" or "write a paper." Lane H covers "prose/article/essay/blog post" but not "paper."

This finding has two implications. First, it is direct, observed evidence for the marker-vocabulary coverage gap discussed in Section 15. Second, it is a demonstration that the journey position loss problem can affect the JMT system itself: the system cannot navigate its own paper-writing task using its current marker vocabulary.

We report this finding without modification. It is not an anomaly to be explained away; it is a concrete data point that the evaluation methodology (Section 12) must include.

### 11.2 Overview

The /go pipeline is the reference host for the JMT implementation. It is a real running system in the quark-studio repository. The case study described here is grounded in one observed run trace; it does not constitute a controlled experiment or a benchmark result.

### 11.3 A JMT-Active Pipeline Run (OBSERVED)

The JMT layer was installed in a pipeline run whose purpose was to build the JMT layer itself: the system bootstrapped its own navigation layer. The global map records the following journey_history.jsonl entry from that run [OBSERVED, verbatim]:

```json
{"run_id": "go_go_ultracode_run_install_journey_2026_06_13", "lane": "A", "milestone": "self-prompt compiler", "progress_made": true, "progress_type": "BUILD_ARTIFACT", "evidence": ["artifact_changed", "gate_passed", "test_added", "changed_files=1"], "blocker": null, "release_verdict": "PASS"}
```

Walking through the five JMT stages for this run:

**Positioning.** The raw goal was to install the Journey Map Thinking layer. The positioner ran deterministic marker-matching and returned north_star_relevance=high, likely_lanes=["A"], can_advance_now=True. Lane A (Recursive /go Prompt Loop) matched because the task involves building the core prompt loop component.

**Lane Selection.** Given lane A and the latent ambition (building the self-prompt compiler as part of the navigation layer), the selector returned primary_lane="A", selected_milestone="self-prompt compiler", progress_type=BUILD_ARTIFACT, artifact_that_proves_progress="changed_files and test_added in the JMT module".

**Gate Alignment.** After the planner produced spec.md, the gate aligner produced journey_gate_alignment.json specifying success_condition="artifact_changed AND test_added AND gate_passed", planned_artifacts=["schema.py", "lanes.py", "cli.py", "tests/test_journey_map.py"], required_tests=["tests/test_journey_map.py"].

**Progress Check.** After the QA evaluator passed, the progress check read the QA report (verdict starting with "PASS") and the release verdict ("PASS"). Concrete signals present: artifact_changed, gate_passed, test_added, changed_files=1. progress_made=True, progress_type=BUILD_ARTIFACT. Exit code: 0.

**Map Update.** The update stage committed the run to journey_history.jsonl (the entry above), updated current_position.md, and confirmed no new blockers.

### 11.4 Owner-Dependent Lane Handling (OBSERVED)

The global blocker_map.json records two owner-dependent blockers [OBSERVED]:

- **Lane I (System Guardian).** Blocker: "earlyoom.service inactive; owner action required." The system emits an owner-unlock packet and halts autonomous work on lane I. Owner-independent work on other lanes (A, B, C, D, etc.) continues in parallel.
- **Lane M (Production Activation).** Blocker: "owner opt-in + production approval required." The system emits an owner-unlock packet and halts autonomous work on lane M.

This is the JMT safety valve for human-in-the-loop gates: the system does not attempt to autonomously enable services or activate production. It names the blocker, emits the packet, and proceeds with what it can do without human action.

---

## 12. Evaluation: Results Obtained and Methodology for the Unrun Metrics

Two empirical results have been obtained: the software mechanism has been verified by two independent toolchains, and the frozen-position anchor has been tested in its target post-compaction regime. The eleven project-level metrics M1 through M11 have not been measured and remain forward-looking.

### 12.1 Results Obtained: Software Mechanism (Two Independent Toolchains)

The reference implementation (11 files, 2,017 lines) was verified by two independent toolchains. A Claude-based run of the test suite produced 26 passed in 0.10s, exit code 0 (Python 3.14.4, pytest-9.0.3). An independent reproduction by a non-Claude Codex toolchain via the claude-code-codex-bridge in a read-only sandbox produced 26 passed, 1 warning in 0.09s, exit code 0, verbatim-stdout SHA256 ad144a9aaa754f6070b552544dae4d509955931175813e0e11b0f0dd5e3188b7. Both runs targeted the same 11 files and 2,017 lines. This satisfies the two-clock standard: two independent toolchains agree on the result.

Four behavioral probes fired as specified. Input "fix a typo" produced relevance low with no lane inflation. Input "what is the current status" produced an anti_loop_warning. Input "end all disease" produced must_pick_concrete_slice=true. A summary-only run produced progress_made=false and recommended_release=BLOCKED_NO_PROGRESS. These probes verify that the code behaves as specified; they do not evaluate whether the design is optimal or novel. The algorithm formalizes the existing deterministic procedure. Full record: paper/journey_map_evidence.md Section 2.

### 12.2 Results Obtained: The Frozen-Position Anchor in the Memory-Loss Regime (Pre-Registered, Powered, Null)

The frozen-position anchor was evaluated in three successive experiments, with each result informing the next. The full record is in paper/journey_map_evidence.md Sections 3, 3b, 3c, RECONCILIATION, and evidence/PREREGISTRATION_postcompaction_v2.md.

**In-context study (Section 3 of the dossier).** Eight control trials and eight treatment trials, both with the plan still in context. Control held_place 1.0 (8/8), treatment held_place 1.0 (8/8), delta 0.0. Null with ceiling effect: both arms scored perfectly because the plan was never lost. Run 1 was discarded as a rate-limit infrastructure failure; Run 2 is the usable dataset.

**Weak-handoff A/B (Section 3b of the dossier).** Control n=8 held_place 0.75 (6/8), treatment n=8 held_place 1.0 (8/8), delta +0.25. The entire measured effect lived in one scenario (P1 sequencing). The baseline was a casual approximately 150-word handoff summary. N=8, directional, not conclusive.

**Pre-registered, powered, real-/compact A/B (Section 3c of the dossier, primary result).** Pre-registered before running. 12 scenarios across 5 loss-types, 4 repetitions per arm per scenario, 48 trials per arm, 96 trials total, 0 dropped. Resume agents drawn from haiku, sonnet, and opus. Judge on sonnet, blind to condition, judge not the trial agent. Baseline was a high-fidelity replica of the real Claude Code /compact 9-section summarizer.

Primary endpoint held_place: control 0.708 (34/48), 95% Wilson CI [0.568, 0.818]; treatment 0.750 (36/48), 95% Wilson CI [0.612, 0.851]; delta +0.042; Fisher exact two-tailed p=0.819. NOT statistically significant (CIs overlap heavily).

Secondary endpoint correct_next_action: control 0.750, treatment 0.750, delta 0.000; Fisher exact two-tailed p=1.000. IDENTICAL.

Per-loss-type held: ordering 12/12 vs 12/12 (ceiling both arms); rationale 8/8 vs 8/8 (ceiling both arms); do_not_repeat 10/12 vs 12/12 (the only non-zero difference, 2 trials, not significant); constraint 4/8 vs 4/8; blocker_state 0/8 vs 0/8.

Per-tier held: haiku 8/12 vs 9/12; sonnet 17/24 vs 18/24; opus 9/12 vs 9/12.

A cross-family replication by a non-Claude Codex toolchain covered 3 clean scenarios (O1, D1, R1) across 2 arms (6 trials); control 3/3 correct, treatment 3/3 correct, delta 0. Delegation IDs: bbf06bc1, 8e471258, 143239d4, 661c2875, e0c4c334, 7e4303bd. Small N, confirmatory.

**Reconciliation.** The +0.25 directional result from the weak-handoff study was an artifact of the weak baseline: the effect was concentrated in one sequencing scenario. When the baseline is upgraded to the real /compact mechanism, the effect vanishes. The powered A/B (48/arm, 96 total, pre-registered) is the operative result for the question "does the anchor beat Claude Code's own compaction for next-action recovery?" The answer is no. The mechanism is that real /compact produces a 9-section summary with dedicated Pending Tasks, Current Work, and Optional Next Step sections; all 12 summaries named the committed next step unambiguously, making the anchor redundant.

**Honest ceiling.** The software mechanism is STRONG (two-clock verified). The cognitive anchor is NOT SUPPORTED against the real /compact baseline (powered null). The anchor's only defensible remaining value is in regimes /compact does not cover: a brand-new session with no compaction summary at all, and structured long-horizon lane and gate positioning that a prose summary may not preserve. Neither regime was tested.

Validity caveat: summaries B1, B2, and C2 reframed or advanced the committed step versus the pre-registered ground truth, so both arms scored 0 on those scenarios. This depresses absolute rates equally in both arms; it does not bias the delta.

### 12.3 Methodology for the Unrun Project-Level Metrics: Study Design

The proposed evaluation is a controlled comparison between two conditions applied to the same set of pipeline tasks:

- **JMT-active (QAH_GO_JOURNEY_MAP=1):** The five JMT stages run as described in Section 7.
- **JMT-baseline (QAH_GO_JOURNEY_MAP=0):** The eleven host stages run without any navigation layer; the pipeline is byte-for-byte the same as Figure 1.

Existing agent benchmarks (AgentBench [15], SWE-bench [16], WebArena [17], GAIA [18], tau-bench [19]) do not directly measure journey-position awareness, lane accuracy, or blocker surfacing. A new annotation protocol is needed to label task inputs with their correct lanes and milestones and to rate progress claims as concrete vs vague.

evaluation_plan.md exists at the paper directory alongside this draft [OBSERVED]; its contents mirror the metrics and hypotheses defined here.

### 12.4 The Eleven Metrics and Hypotheses

**M1: Lane Identification Accuracy.**
Definition: Given a set of labeled task inputs (each labeled with its correct primary lane by a human annotator), the fraction of tasks for which the JMT positioner returns the correct lane as its primary lane.
Hypothesis H1: When QAH_GO_JOURNEY_MAP=1, lane identification accuracy exceeds a random baseline (uniform over 14 lanes, approximately 7%) for in-vocabulary tasks.
Data required: A held-out set of task descriptions annotated with the correct primary lane by an expert familiar with the 14-lane taxonomy.

**M2: Milestone Selection Accuracy.**
Definition: Given lane-labeled tasks for which the correct milestone is known, the fraction for which the select-lane stage selects the annotator-agreed milestone.
Hypothesis H2: For tasks in lanes with clear marker vocabulary, milestone selection accuracy exceeds chance.
Data required: Per-task annotated correct milestone, conditional on correct lane.

**M3: Gate-Alignment Correctness.**
Definition: The fraction of pipeline runs where the planned artifacts and required tests specified in journey_gate_alignment.json are judged sufficient (by a human reviewer of the QA report) to verify the selected milestone.
Hypothesis H3: Gate alignment reduces the rate of QA reports that cite "missing artifact" as a failure reason.
Data required: Human annotation of QA reports for artifact coverage.

**M4: No-Progress-Loop Reduction.**
Definition: The fraction of pipeline runs that terminate in BLOCKED_NO_PROGRESS, measured in JMT-active vs JMT-baseline conditions.
Hypothesis H4: JMT-active runs have a lower rate of no-progress loops than JMT-baseline runs on the same task set.
Data required: Paired run logs (JMT on vs JMT off) for the same task set.

**M5: Blocker-to-Unlock Conversion Rate.**
Definition: Given a set of runs that terminated with a named blocker in blocker_map.json, the fraction that subsequently produced the stated next_unlock artifact and advanced the lane.
Hypothesis H5: Explicit blocker naming increases the rate at which follow-up runs produce the required unlock artifact.
Data required: Run history with blocker states and follow-up run outcomes.

**M6: Artifact Completion Rate.**
Definition: The fraction of pipeline runs where all planned_artifacts listed in journey_gate_alignment.json are present and non-empty at the time the release gate fires.
Hypothesis H6: JMT gate alignment increases artifact completion rate compared to runs without gate alignment.
Data required: File system inspection at release gate time, paired with gate alignment plans.

**M7: QA Pass Rate.**
Definition: The fraction of pipeline runs where the QA verdict starts with "PASS" (PASS or PASS_WITH_WARNINGS), measured in JMT-active vs JMT-baseline conditions.
Hypothesis H7: JMT gate alignment and progress check increase the QA pass rate by ensuring the generator targets gate conditions explicitly.
Data required: QA verdict strings from paired runs.

**M8: Unsupported-Claim Reduction.**
Definition: The fraction of generated artifacts in which an independent reviewer identifies at least one unsupported empirical claim, measured in JMT-active vs JMT-baseline conditions.
Hypothesis H8: Honest-scope footers and blocked_claims lists in JourneyGateAlignment reduce the rate of unsupported claims in generator output.
Data required: Human review of generated artifacts for unsupported claims.

**M9: Next-Action Executability.**
Definition: The fraction of journey_progress_check.json next_unlock values that an independent agent (or human executor) can execute without requesting clarification.
Hypothesis H9: The concrete-signal requirement for progress_made forces next_unlock values to be more specific and executable than free-form agent-generated next steps.
Data required: Human rating of next_unlock executability on a binary scale.

**M10: Repeated-Run Avoidance.**
Definition: Given paired runs on the same task, the fraction of JMT-active runs that avoid repeating a step recorded in what_not_to_repeat (JourneyLaneSelection) compared to JMT-baseline runs.
Hypothesis H10: The what_not_to_repeat field in lane selection reduces the rate of redundant re-execution of completed steps.
Data required: Run traces annotated for step repetition relative to prior runs.

**M11: North-Star Progress Score.**
Definition: A human-annotated ordinal score (0 = no movement, 1 = marginal movement, 2 = clear movement) for each completed run, representing how much the run moved the system closer to NORTH_STAR = "QAH as an Ambition-to-Reality Operating System" on the relevant capability axis.
Hypothesis H11: Runs with JMT active score higher on the North-Star progress scale than JMT-baseline runs on the same tasks.
Data required: Per-run annotated progress scores from a rater familiar with the capability level taxonomy.

---

## 13. Failure Modes and Safety Boundaries

### 13.1 The Six Honesty Boundaries

The JMT framework ships with six explicit honesty boundaries, each encoded as a structural constraint rather than a policy document.

**(a) JMT is not general intelligence.** JMT is a deterministic marker-matching and boolean-signal layer. It does not reason, plan, or generate. Any complex understanding of what a task means comes from the host pipeline, not from JMT.

**(b) JMT does not remove the need for planning.** The gate alignment stage reads a plan produced by the host planner. JMT does not generate the plan; it aligns gate conditions to an existing plan. Removing the planner from the host pipeline would leave the gate alignment stage with no input to read.

**(c) JMT does not guarantee correctness.** A progress check that returns progress_made=True only guarantees that a concrete signal was detected. It does not guarantee that the artifact is correct, the test is meaningful, or the gate condition was actually satisfied in the intended sense.

**(d) JMT does not replace QA.** The JMT progress check reads the QA report; it does not replace it. The QA/Evaluator stage remains the arbiter of artifact quality. JMT reads the QA verdict to determine whether a gate was passed; it does not independently verify the artifact.

**(e) JMT can over-map or under-map tasks that are not in the marker vocabulary.** The real observed negative finding (Section 11.1) demonstrates under-mapping: the task of writing this paper returned relevance=low, lanes=[]. Under-mapping can cause the pipeline to proceed without navigation context when navigation context would be beneficial. Over-mapping is also possible: a task that superficially matches a lane's markers but is not genuinely in that lane's scope can be routed to the wrong lane, producing a gate alignment and progress check that are not relevant to the actual work.

**(f) The project-level hypotheses are forward-looking and need empirical evaluation before strong claims can be made.** The software mechanism has been verified (Section 12.1) and the frozen-position anchor has been tested in the post-compaction regime (Section 12.2). However, the eleven project-level metrics and hypotheses in Sections 12.3 and 12.4 are a methodology, not results. The claim that JMT reduces no-progress loops (H4) or increases QA pass rate (H7) is a hypothesis. No labeled task bank, lane annotation dataset, or paired JMT-active vs JMT-baseline project-level experimental run exists to support or refute these hypotheses at the time of this writing.

### 13.2 The No-Progress Guard in Practice

When progress_made is False, the JMT progress check produces [OBSERVED from progress.py]:

```
progress_type: BLOCKED_NO_SAFE_ACTION
recommended_release: BLOCKED_NO_PROGRESS
next_unlock: "produce a concrete artifact or report a true blocker; never record a summary"
```

The exit code is 1 (non-zero), which the pipeline host can use to trigger a BLOCKED_NO_PROGRESS release verdict. This prevents the pipeline from recording a release PASS when no real progress occurred.

### 13.3 Owner-Dependent Safety Valve

Owner-dependent lanes (I and M in the current implementation [OBSERVED from lanes.py]) represent actions that require human authorization before autonomous execution can proceed. When the positioner detects an owner-dependent lane or the selector confirms it, the system:

1. Emits an owner-unlock packet (progress_type=CREATE_OWNER_PACKET).
2. Records the blocker in blocker_map.json with owner_dependent=True and the required next_unlock.
3. Continues with owner-independent work in parallel lanes.
4. Does not attempt to perform the owner-gated action autonomously.

This is a conservative safety posture: the system would rather halt on an owner-dependent gate than take an unauthorized action.

### 13.4 The Honest-Scope Footer as Structural Prevention

Every JMT artifact carries honest_scope: PROVISIONAL_JOURNEY_MAP_NO_OUTPUT_QUALITY_GUARANTEE and scope_walls_certified: false. This is not a disclaimer appended to a finished claim; it is a field in every dataclass that is written unconditionally by the artifact I/O layer [OBSERVED from artifacts.py and schema.py]. A downstream consumer that reads these fields knows the artifact is provisional. A consumer that ignores them is proceeding without reading the artifact's stated epistemic status.

---

## 14. Discussion

The sections above specify how JMT works. This section addresses why the design choices were made as they were, and what they cost, in terms the practitioner who must decide whether to adopt the framework needs to weigh. The failure mode at stake is concrete: a pipeline that ran for twenty minutes, produced no changed artifact, and has no record of where it stopped. The discussion below traces each architectural choice back to that failure.

### 14.1 What the Navigation-Position Abstraction Provides

The JMT framework proposes that persistent, typed, gate-checked navigation position is a useful abstraction for long-running agent pipelines, one that is distinct from reasoning quality, memory depth, and tool availability.

The analogy to control systems is instructive. A control system maintains an estimate of the plant's current state; without that state estimate, even a correct control law produces incorrect actuator commands. JMT proposes that agent pipelines need an analogous state estimate: not the state of the environment, but the state of the agent's journey through a predefined capability space. The five JMT artifacts collectively constitute this state estimate, and the progress check plays an analogous role to a state-update rule, without the formal convergence guarantees a control-theoretic law would carry.

The four improvement areas named in the framework's design requirements (Section 4.5) each map to a specific JMT component, proposed (not measured) as the mechanism that addresses the corresponding failure mode:

| Improvement Area | JMT Component | Mechanism (proposed) | Failure Mode Addressed |
|---|---|---|---|
| Agent alignment to declared intent | Journey Map Positioning (position subcommand); north_star_relevance field | When relevance is low or none, must_pick_concrete_slice=True directs the pipeline to ground the task before proceeding | Failure mode 4.3(a): infinite refinement without artifact grounded in the North Star |
| Progress tracking | Journey Progress Check (progress subcommand); concrete-signal detection in progress.py | progress_made=True requires at least one concrete signal; absence forces BLOCKED_NO_SAFE_ACTION | Failure mode 4.3(c): prose-summary progress claim |
| Blocker handling | Blocker Map (blocker_map.json); owner-dependent valve in selector.py | Named blockers persist across runs; owner-dependent blockers halt autonomous action and emit an owner-unlock packet | Failure mode 4.3(d): blocker amnesia |
| Evidence-gated execution | Journey Gate Alignment (align-gate subcommand); gate pass condition in progress.py | Gate passes only when QA verdict starts with PASS or release verdict is PASS or PASS_WITH_WARNINGS [OBSERVED from progress.py] | Failure mode 4.3(b): repeated-step execution without gate verification |

All entries in the Mechanism column are proposed design intents, not measured results. The hypotheses that operationalize these proposals are H4, H6, H7, and H3 respectively in Section 12.

The analogy to operating system process scheduling is also relevant. An OS scheduler must know which process is in which state (running, waiting, blocked) to make correct scheduling decisions. Without this state, the scheduler cannot distinguish a process that is making progress from one that is spinning. The JMT progress check is, in this framing, the mechanism that distinguishes a productive pipeline run from a spinning one.

The frozen-position anchor design (Section 4.2) gives the agent something it cannot otherwise obtain from raw conversation history: a stable, typed, re-readable snapshot of where it is. This snapshot is the mechanism that makes JMT a prompt technique in addition to a navigation substrate. The agent is not a passive consumer of JMT artifacts; it is an active reader that consults the frozen position at each pipeline entry. The distinction matters because it means JMT's value is not only in the artifacts it produces, but in the discipline of reading them.

### 14.2 Determinism vs Coverage

The most significant trade-off in the current implementation is between determinism and coverage. Deterministic marker-matching is predictable and auditable: given the same task description, the positioner always produces the same output. But determinism comes at the cost of coverage: tasks described in vocabulary that does not match any lane's markers will be unmapped, as the negative finding demonstrates.

This trade-off is not unique to JMT. Any rule-based system faces the generalization problem. The difference is that JMT makes the gap visible: an unmapped task returns relevance=low and lanes=[], which is a clear signal that the navigation layer has no position for this task. An implicit navigation system provides no such signal.

### 14.3 Honest-Scope Discipline as a Structural Mechanism

Prior work on agent QA (AgentBench [15], tau-bench [19]) evaluates output quality after the fact. JMT embeds an honest-scope declaration in every artifact at write time, preventing a downstream consumer from treating a provisional navigation artifact as a certified result without requiring a separate review step.

The Reflexion [3] and Self-Refine [11] systems improve output quality through post-hoc verbal critique. JMT's honest-scope footer is complementary: it does not critique the quality of the artifact, but it does prevent the artifact from being treated as something it is not.

### 14.4 Positioning JMT Relative to Reflexion and Voyager

Reflexion [3] stores verbal self-reflections in episodic memory and uses them to improve subsequent attempts within a session. The persistence is at the level of verbal critique, not structural navigation state. JMT's persistence is at the level of typed JSON artifacts: lane, milestone, gate condition, progress signal, blocker. These are not improvements on prior verbal output; they are a record of where the agent is and what it needs to do next.

Voyager [12] accumulates a skill library of verified executable programs, enabling an agent to reuse prior capabilities in novel situations. The persistence is at the level of skills (what the agent can do). JMT's persistence is at the level of position (where the agent is). These are complementary: an agent with a rich skill library but no navigation position can have the tools to do the work without knowing which work to do next.

### 14.5 The Anti-Loop Guard and Formal Verification Precedent

The no-progress guard in JMT (Section 9.4) is analogous to liveness properties in formal verification: a property asserting that the system eventually makes progress. Continuous integration (CI) systems enforce a related property: a build is not "done" until all tests pass and the artifact is present. JMT applies the same logic at the pipeline level: a run is not "progress" until a concrete artifact signal is detected.

This is a design choice with costs. The concrete-signal requirement can be satisfied by a trivially created file (a degenerate case). Adversarial testing of the no-progress guard, to determine whether trivial signals can game it, is a future work item (Section 16).

### 14.6 Addressing the Two Primary Objections

Two objections recur in early reviews of this framework. Each is stated here at its strongest and answered directly.

**Objection 1 (Prompt Template Objection):** A well-written prompt template specifying lane, milestone, and gate conditions achieves the same navigation benefit as 2,017 lines of Python, at zero engineering cost.

**Answer:** Although a prompt template can carry the same vocabulary, it cannot enforce the same properties across runs. The warrant has three parts. First, a prompt template is rewritten at each run's compilation time by the LLM that may itself be disoriented; a Python module is not rewritten by the agent and cannot hallucinate a routing decision. Second, the no-progress guard (Section 9.4) requires concrete filesystem signals and emits exit code 1 on failure, which the pipeline host can branch on mechanically; a prompt has no equivalent exit-code path. Third, the blocked_claims list in JourneyGateAlignment prevents the generator from making claims its lane cannot support; a template has no structural enforcement equivalent. These are auditable differences, not merely stylistic ones.

**Objection 2 (Empirics Objection):** A paper that proposes eleven hypotheses and measures none of them has not yet established that the framework does what it claims.

**Answer:** Two empirical results have now been obtained. The software mechanism is verified by two independent toolchains (26/26 tests, exit code 0, Claude and a non-Claude Codex reproduction; four behavioral probes firing as specified). The frozen-position anchor has been measured against Claude Code's own /compact in a pre-registered, powered A/B (96 trials), returning a null: the anchor adds no measurable next-action-recovery benefit over /compact, which already preserves the committed next step. The broad eleven-metric project-level study (M1 through M11) remains precondition-bounded future work. The labeled datasets and annotation protocols of Section 12.3 do not yet exist, so premature measurement would confound results. The evaluation methodology is the precondition for valid measurement. Proposing the taxonomy before collecting data is the correct epistemic order. The project-level hypotheses are not yet confirmed.

### 14.7 The Honest Scope of This Work Is Its Strongest Claim

A framework that accurately reports what it does not do, encodes the report structurally rather than as a footnote, and ships a negative finding as a section header rather than hiding it is making an affirmative argument about engineering honesty. That is the contribution the evaluation methodology in Section 12 is designed to test. The software mechanism is empirically verified (Section 12.1) and the frozen-position anchor has been measured against Claude Code's own /compact in a pre-registered, powered study returning a null (Section 12.2). The project-level benefits (M1 through M11) remain proposals and forward-looking framings and have not been measured.

---

## 15. Limitations

The following limitations are not hedges appended to protect the authors; they are the honest engineering boundary without which the contribution claims would be overclaims.

### 15.1 Lead Limitation: Marker-Vocabulary Coverage Gap (OBSERVED)

The most concrete and immediately observed limitation of the current implementation is its marker-vocabulary coverage gap. When the JMT positioner was run on the task of writing this paper, it returned [OBSERVED]:

```
OK: relevance=low lanes=[] owner_dependent=False anti_loop=False
```

The marker vocabulary has no entry for "research paper," "write a paper," "academic paper," or related phrasings. Lane H covers "prose/article/essay/blog post" but not "paper." This means that a task of significant scope and consequence is, from the positioner's perspective, unmapped. The system cannot navigate it.

This is an engineering limitation requiring vocabulary expansion. It is not a fundamental flaw in the navigation-position abstraction; it is a gap in the current marker dictionary. But it is a real gap, observed on a real task, and it cannot be dismissed.

### 15.2 Scope of the Empirical Results Obtained

Two empirical results were obtained. First, the software mechanism: verified by two independent toolchains (26/26 tests, exit code 0, Claude and a non-Claude Codex reproduction; four behavioral probes firing as specified). Second, the frozen-position anchor: tested in a powered, pre-registered A/B (96 trials, 48 per arm) against the real Claude Code /compact baseline, returning a null: the anchor is redundant with /compact for next-action recovery (correct-next-action delta 0.000, held-place delta +0.042, neither statistically significant). The broad eleven-metric project-level study (M1 through M11) remains unrun. No labeled dataset exists, no lane-annotated task bank has been produced, and no paired JMT-active vs JMT-baseline project-level runs have been conducted. The hypotheses H1 through H11 are forward-looking and should be treated as such until evidence supports or refutes them. Additionally, the anchor's potential value in the no-summary cross-session regime (where no /compact output exists at all) and in structured long-horizon lane and gate positioning is untested. The behavioral probes in Section 12.1 verify that the mechanisms fire at the unit level; they do not measure project-level metric reductions such as fewer no-progress loops across a real multi-session project.

### 15.3 Single-System Reference Implementation

The case study in Section 11 uses one pipeline (/go in the quark-studio repository) in one configuration. Generalizability to other agent pipelines, other host systems, or other domains is untested. The claim that JMT "interleaves five stages into any existing agent pipeline" is a design claim, not a verified empirical claim.

### 15.4 Static Lane Set

The 14 lanes (A through N) are manually authored and encode the current structure of one system. Adding a new lane requires engineering work: writing the lane definition, adding marker vocabulary, writing tests, and seeding the global map. There is no mechanism for automatic lane discovery from observed task types.

### 15.5 Deterministic Routing Under Semantic Variation

The marker-matching approach can fail to route semantically equivalent task phrasings that use different vocabulary. Semantic routing (embedding-based or LLM-assisted lane assignment) is a future work item.

### 15.6 Adversarial Pressure on the No-Progress Guard

A trivial file change (such as creating an empty file or writing a timestamp) would technically satisfy the changed-file signal without producing meaningful progress. No adversarial testing of this guard has been conducted.

### 15.7 Owner-Gate Automation Gap

Owner-dependent gates (lanes I and M) require human action before the corresponding work can proceed. The mechanism for notifying the owner, tracking whether the owner has acted, and re-engaging the pipeline after owner action is outside the scope of the current implementation.

---

## 16. Future Work

**1. Running the project-level evaluation metrics.** The post-compaction A/B has been run (Section 12.2) and returned a null against /compact for next-action recovery. The remaining empirical work has two parts: (a) the project-level M1 through M11 paired study, which requires building a labeled task bank with expert-annotated correct lanes and milestones, producing paired run logs (JMT-active vs JMT-baseline), and training annotators on the JMT taxonomy; and (b) the two regimes /compact does not cover: a brand-new session with no compaction summary at all (where any persisted note trivially beats nothing), and structured long-horizon lane and gate positioning that a prose summary may not preserve.

**2. Expanding the marker vocabulary.** The negative finding (Section 15.1) demonstrates a vocabulary gap for research and academic task types. Add "paper," "study," "literature review," "experiment," and related terms; guide expansion by systematic analysis of tasks returning lanes=[] in practice.

**3. Semantic routing as a complement to deterministic matching.** Embedding-based or LLM-assisted lane assignment could complement marker-matching. An ablation study comparing deterministic-only, semantic-only, and hybrid routing would clarify the coverage-vs-predictability trade-off.

**4. Generalization to other agent pipelines.** Porting JMT to other pipeline architectures (different planners, different QA stages, different release gates) would test the design claim that the five-stage layer can interleave into any multi-step agent pipeline.

**5. Adversarial testing of the no-progress guard.** Systematic testing with degenerate artifact strategies would reveal whether the current signal set is sufficient or whether additional signals (semantic change detection, test-coverage delta) are needed.

**6. Multi-agent extension.** A shared journey map across parallel agent tracks, where blockers from one agent are visible to others, is a natural extension for multi-agent systems like AutoGen [5].

**7. Dynamic lane addition from observed task types.** An auto-extension mechanism that proposes new lanes based on tasks repeatedly returning lanes=[] would allow the lane set to grow with the system, subject to a determinism-preserving review protocol.

**8. Integration with existing benchmarks.** Measuring JMT-active vs JMT-baseline on SWE-bench [16] and tau-bench [19] would test whether navigation-position awareness affects benchmark performance.

**9. Extending the Journey Map bundle.** The Journey Map program currently comprises the navigation substrate (journey_map), the go_loop, latent_ambition, dynamic_prompt_tailor, and book_procedures pipeline stages. Formalizing the interaction contracts between these stages and the navigation substrate would allow frozen position artifacts to be consumed as structured context rather than optional advisory input.

---

## 17. Conclusion

Return to the practitioner in Section 2, watching an agent loop for twenty minutes, producing careful analysis and well-formatted plans, advancing nothing. With JMT active on that run, the agent would have read a frozen position record at the start: it knows its lane, its target milestone, the gate condition it must satisfy, and the concrete artifact that proves progress. The loop does not disappear, but it cannot run silently. The no-progress guard fires. The pipeline host branches. The practitioner sees a named blocker, not a blank context window. That is the difference the navigation layer is designed to make, and it is the difference the evaluation methodology in Section 12 is designed to measure.

The algorithm section (Section 10) closes the paper's central argument: the claim that JMT is a coherent, distinct navigation layer is supported not by assertion but by a formal procedure that a skeptical reader can inspect, run, and attempt to falsify. Section 12 presents the two results obtained so far and the methodology for the unrun project-level metrics.

The honest scope of this contribution is bounded by what is in this paper and what is not. What is in: a formal framework, a reference implementation, a formal algorithm, an evaluation methodology blueprint, two empirical results (the software mechanism verified by two independent toolchains in Section 12.1; the frozen-position anchor tested in its target post-compaction regime and found to add no measurable next-action-recovery benefit over Claude Code's own /compact in a pre-registered powered null in Section 12.2), and one observed negative finding (Section 15.1). What is not: the broad eleven-metric project-level study (M1 through M11, future work), generalization evidence, or any claim of superiority over any existing system. The project-level hypotheses are forward-looking; the negative finding is real. The framework's verified value is in the deterministic navigation mechanism: positioning, gating, lane selection, and the no-progress guard. The cognitive anchor is redundant with /compact for next-action recovery and untested in the regimes /compact does not cover.

We invite the agent engineering community to engage with the results obtained (Sections 12.1 and 12.2), to run the eleven project-level metrics (M1 through M11), and to report whether the navigation-position-loss framing names a failure class worth formalizing. The question is open. The methodology to answer it is now specified, and two results anchor it. For ML practitioners running long-horizon evaluation loops, such as SWE-bench or tau-bench pipelines that span multiple container restarts and checkpoint boundaries, navigation position is an additional coordinate orthogonal to task-success rate: recording which lane, milestone, and gate applies to each run is, we argue, a prerequisite for diagnosing why a pipeline loops without advancing its score, and the JMT evaluation methodology is designed to measure exactly that gap.

---

## 18. References

[1] Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc Le, Denny Zhou. "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." Advances in Neural Information Processing Systems (NeurIPS), 2022. arXiv:2201.11903.

[2] Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, Yuan Cao. "ReAct: Synergizing Reasoning and Acting in Language Models." International Conference on Learning Representations (ICLR), 2023. arXiv:2210.03629.

[3] Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, Shunyu Yao. "Reflexion: Language Agents with Verbal Reinforcement Learning." Advances in Neural Information Processing Systems (NeurIPS), 2023. arXiv:2303.11366.

[4] Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L. Griffiths, Yuan Cao, Karthik Narasimhan. "Tree of Thoughts: Deliberate Problem Solving with Large Language Models." Advances in Neural Information Processing Systems (NeurIPS), 2023. arXiv:2305.10601.

[5] Qingyun Wu, Gagan Bansal, Jieyu Zhang, Yiran Wu, Beibin Li, Erkang Zhu, Li Jiang, Xiaoyun Zhang, Shaokun Zhang, Jiale Liu, Ahmed Hassan Awadallah, Ryen W. White, Doug Burger, Chi Wang. "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation Framework." arXiv:2308.08155, 2023.

[6] G. Lynn Shostack. "Designing Services That Deliver." Harvard Business Review, 62(1):133-139, 1984.

[7] Mary Jo Bitner, Amy L. Ostrom, Felicia N. Morgan. "Service Blueprinting: A Practical Technique for Service Innovation." California Management Review, 50(3):66-94, 2008.

[8] Katherine N. Lemon, Peter C. Verhoef. "Understanding Customer Experience Throughout the Customer Journey." Journal of Marketing, 80(6):69-96, 2016.

[9] Lei Wang, Wanyu Xu, Yihuai Lan, Zhiqiang Hu, Yunshi Lan, Roy Ka-Wei Lee, Ee-Peng Lim. "Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning by Large Language Models." Proceedings of the Annual Meeting of the Association for Computational Linguistics (ACL), 2023. arXiv:2305.04091.

[10] Charles Packer, Vivian Fang, Shishir G. Patil, Kevin Lin, Sarah Wooders, Joseph E. Gonzalez. "MemGPT: Towards LLMs as Operating Systems." arXiv:2310.08560, 2023.

[11] Aman Madaan, Niket Tandon, Prakhar Gupta, Skyler Hallinan, Luyu Gao, Sarah Wiegreffe, Uri Alon, Nouha Dziri, Shrimai Prabhumoye, Yiming Yang, Shashank Gupta, Bodhisattwa Prasad Majumder, Katherine Hermann, Sean Welleck, Amir Yazdanbakhsh, Peter Clark. "Self-Refine: Iterative Refinement with Self-Feedback." Advances in Neural Information Processing Systems (NeurIPS), 2023. arXiv:2303.17651.

[12] Guanzhi Wang, Yuqi Xie, Yunfan Jiang, Ajay Mandlekar, Chaowei Xiao, Yuke Zhu, Linxi Fan, Anima Anandkumar. "Voyager: An Open-Ended Embodied Agent with Large Language Models." Transactions on Machine Learning Research (TMLR), 2024. arXiv:2305.16291 (arXiv 2023; published TMLR 2024).

[13] Chris Lu, Cong Lu, Robert Tjarko Lange, Jakob Foerster, Jeff Clune, David Ha. "The AI Scientist: Towards Fully Automated Open-Ended Scientific Discovery." arXiv:2408.06292, 2024.

[14] Joon Sung Park, Joseph C. O'Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, Michael S. Bernstein. "Generative Agents: Interactive Simulacra of Human Behavior." Proceedings of the ACM Symposium on User Interface Software and Technology (UIST), 2023. arXiv:2304.03442.

[15] Xiao Liu, Hao Yu, Hanchen Zhang, Yifan Xu, Xuanyu Lei, Hanyu Lai, Yu Gu, Hangliang Ding, Kaiwen Men, Kejuan Yang, Shudan Zhang, Xiang Deng, Aohan Zeng, Zhengxiao Du, Chenhui Zhang, Sheng Shen, Tianjun Zhang, Yu Su, Huan Sun, Minlie Huang, Yuxiao Dong, Jie Tang. "AgentBench: Evaluating LLMs as Agents." International Conference on Learning Representations (ICLR), 2024. arXiv:2308.03688.

[16] Carlos E. Jimenez, John Yang, Alexander Wettig, Shunyu Yao, Kexin Pei, Ofir Press, Karthik Narasimhan. "SWE-bench: Can Language Models Resolve Real-World GitHub Issues?" International Conference on Learning Representations (ICLR), 2024. arXiv:2310.06770.

[17] Shuyan Zhou, Frank F. Xu, Hao Zhu, Xuhui Zhou, Robert Lo, Abishek Sridhar, Xianyi Cheng, Tianyue Ou, Yonatan Bisk, Daniel Fried, Uri Alon, Graham Neubig. "WebArena: A Realistic Web Environment for Building Autonomous Agents." International Conference on Learning Representations (ICLR), 2024. arXiv:2307.13854.

[18] Gregoire Mialon, Clement Fourrier, Craig Swift, Thomas Wolf, Yann LeCun, Thomas Scialom. "GAIA: A Benchmark for General AI Assistants." International Conference on Learning Representations (ICLR), 2024. arXiv:2311.12983.

[19] Shunyu Yao, Noah Shinn, Pedram Razavi, Karthik Narasimhan. "tau-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains." arXiv:2406.12045, 2024.

[20] Omar Khattab, Arnav Singhvi, Paridhi Maheshwari, Zhiyuan Zhang, Keshav Santhanam, Sri Vardhamanan, Saiful Haq, Ashutosh Sharma, Thomas T. Joshi, Hanna Moazam, Heather Miller, Matei Zaharia, Christopher Potts. "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines." arXiv:2310.03714, 2023.

[21] Timo Schick, Jane Dwivedi-Yu, Roberto Dessi, Roberta Raileanu, Maria Lomeli, Luke Zettlemoyer, Nicola Cancedda, Thomas Scialom. "Toolformer: Language Models Can Teach Themselves to Use Tools." Advances in Neural Information Processing Systems (NeurIPS), 2023. arXiv:2302.04761.


---

*honest_scope: PROVISIONAL_PAPER_DRAFT_NO_OUTPUT_QUALITY_GUARANTEE*
*scope_walls_certified: false*