# Roadmap

Four phases, each with a concrete deliverable. Phases 1, 3, and 4 are the minimum viable
version of this project (see the scope guard in `01-overview.md`); Phase 2 is the
differentiator if time allows.

## Phase 1 — Harness (1-2 weeks)

- Wrap the target agent (OrbitDesk) behind a thin HTTP API that garak can call.
- Run garak's standard probe set against it.
- Capture every (attack, response) pair to storage, with probe metadata.

**Deliverable**: a working attack → response log. No scoring yet.

## Phase 2 — Detection layer (1-2 weeks)

- Implement one detector that can be explained and defended in depth — an attention-shift or
  embedding-similarity classifier, not just a call to garak's built-in judge.
- Add a grounding/citation check, reusing OrbitDesk's verification-node pattern.
- Measure the detector's own precision/recall against a labeled subset of JailbreakBench and
  the deepset prompt-injection dataset.

**Deliverable**: a detector with a reported precision/recall table.

## Phase 3 — Benchmark & scoring (1 week)

- Run the full pipeline (attack runner → target agent → detection layer) against
  JailbreakBench's 100 behaviors and StrongREJECT's rubric.
- Report Attack Success Rate (ASR) before and after the detection layer — this delta is the
  project's headline number.

**Deliverable**: a results table/CSV with real, reproducible numbers.

## Phase 4 — Dashboard & writeup (1 week)

- Build the React/TS dashboard: ASR by category, detector confusion matrix, annotated example
  transcripts.
- Write the README: methodology, citations to `04-research-references.md`, and a disclosed-
  limitations section (mirroring OrbitDesk's disclosure pattern).

**Deliverable**: a deployed, clickable dashboard plus a README a recruiter or interviewer can
read end-to-end.

## Estimated total

4-6 weeks at a sustained but non-intensive pace, run in parallel with coursework — matching
the "no imposed deadline" framing in the overview.
