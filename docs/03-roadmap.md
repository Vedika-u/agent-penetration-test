# Roadmap

Five phases, each with a concrete deliverable. Phase 1 is new work created by the decision to
build the target agent from scratch instead of reusing OrbitDesk, and is not optional —
everything downstream depends on it existing. Phases 1, 2, 4, and 5 are the minimum viable
version of this project (see the scope guard in `01-overview.md`); Phase 3 is the
differentiator if time allows.

## Phase 1 — Target agent (1-2 weeks)

- Build the target agent from scratch: a LangGraph state graph (agent → tool → memory →
  response loop).
- Implement the three tools: `web_search`, `notes` (SQLite-backed, persists across turns),
  `calculator`.
- Add a minimal verification node (basic grounding check only — the full detection layer is
  Phase 3).
- Expose the agent over HTTP.

**Deliverable**: a working multi-turn agent, reachable over HTTP, manually verified against a
handful of benign tasks (e.g. "search for X and save a note", "recall what I asked you to
remember earlier").

## Phase 2 — Harness (1 week)

- Wrap the Phase 1 target agent's HTTP API so garak can call it.
- Run garak's standard probe set against it.
- Capture every (attack, response) pair to storage, with probe metadata.

**Deliverable**: a working attack → response log. No scoring yet.

## Phase 3 — Detection layer (1-2 weeks)

- Implement one detector that can be explained and defended in depth — an attention-shift or
  embedding-similarity classifier, not just a call to garak's built-in judge.
- Extend the target agent's verification node into a full grounding/citation check.
- Add a memory-integrity check on the `notes` tool, since persistent memory is this agent's
  distinct (vs. a stateless target) attack surface.
- Measure the detector's own precision/recall against a labeled subset of JailbreakBench and
  the deepset prompt-injection dataset.

**Deliverable**: a detector with a reported precision/recall table.

## Phase 4 — Benchmark & scoring (1 week)

- Run the full pipeline (attack runner → target agent → detection layer) against
  JailbreakBench's 100 behaviors and StrongREJECT's rubric.
- Report Attack Success Rate (ASR) before and after the detection layer — this delta is the
  project's headline number.

**Deliverable**: a results table/CSV with real, reproducible numbers.

## Phase 5 — Dashboard & writeup (1 week)

- Build the React/TS dashboard: ASR by category, detector confusion matrix, annotated example
  transcripts.
- Write the README: methodology, citations to `04-research-references.md`, and a disclosed-
  limitations section covering both the detection layer's limits and the target agent's own
  design choices (why these three tools, why this memory model).

**Deliverable**: a deployed, clickable dashboard plus a README a recruiter or interviewer can
read end-to-end.

## Estimated total

5-8 weeks at a sustained but non-intensive pace, run in parallel with coursework — matching
the "no imposed deadline" framing in the overview. The added week (vs. reusing OrbitDesk)
comes entirely from Phase 1.
