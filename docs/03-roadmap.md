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

*Shipped.* `src/harness/{run.py,ingest.py,storage.py}`; validated end-to-end against the live
target agent (found and fixed a real bug in the process: garak logs each attempt twice, once
generated and once scored, under the same UUID — `ingest_report` now keeps only the scored copy).
A second real bug surfaced running a larger 256-prompt sweep (`probes.dan.DanInTheWild`): a single
slow multi-tool-call turn exceeded `configs/rest_generator.json`'s 120s `request_timeout` and
garak aborted the entire run rather than skipping one slow attempt — fixed by raising the timeout
to 300s (see the setup doc's troubleshooting table).

## Phase 3 — Detection layer (1-2 weeks)

- Implement one detector that can be explained and defended in depth — an attention-shift or
  embedding-similarity classifier, not just a call to garak's built-in judge.
- Extend the target agent's verification node into a full grounding/citation check.
- Add a memory-integrity check on the `notes` tool, since persistent memory is this agent's
  distinct (vs. a stateless target) attack surface.
- Measure the detector's own precision/recall against a labeled subset of JailbreakBench and
  the deepset prompt-injection dataset.

**Deliverable**: a detector with a reported precision/recall table.

*Shipped.* Embedding-similarity chosen over attention-shift (Ollama exposes no attention
weights — see `src/target_agent/detection/injection_detector.py`'s docstring). Measured
precision 0.661 / recall 0.820 / F1 0.732 on a 196-example held-out mix of
deepset/prompt-injections and JailbreakBench/JBB-Behaviors, with a 40-phrase reference set — see
`reports/phase3_detector_eval.md` for full methodology and caveats, including an honest finding
worth flagging: expanding the reference set from an initial 26 phrases to 40 (more attack styles
covered) measurably *reduced* precision/F1 (0.757 → 0.732) rather than improving it, reported
as-is rather than reverted. Grounding/claim check and
the notes memory-integrity check are both implemented in `verification.py` /
`tools/notes.py` / `memory/db.py`, and the injection detector is wired live into the graph's
`verify` node (not just an offline eval module).

## Phase 4 — Benchmark & scoring (1 week)

- Run the full pipeline (attack runner → target agent → detection layer) against
  JailbreakBench's 100 behaviors and StrongREJECT's rubric.
- Report Attack Success Rate (ASR) before and after the detection layer — this delta is the
  project's headline number.

**Deliverable**: a results table/CSV with real, reproducible numbers.

*Shipped, at full scale.* `src/harness/run_benchmark.py` ran all 100 of JBB-Behaviors' behaviors
across 3 attack templates, judged by `phi3-mini-gguf` (a different model/weights than the
target's own `llama3.2`, removing the earlier same-model-judge weakness). Real, reproducible
result: ASR 0% → 0% (before/after detection) — a genuine ceiling effect, not a bug: `llama3.2`
refused all 100 attempts, so there was nothing for the detection layer to catch. An earlier
20-behavior run with a same-model judge had measured a non-zero 5% baseline (one "success");
re-running that same behavior at full scale under the independent judge shows a clean refusal,
suggesting the earlier result was very likely a same-model-judge artifact rather than a real
vulnerability the detector then closed. See `reports/phase4_benchmark.md`'s "Notable observation"
section for the full analysis, including verification that the judge itself wasn't stuck (tested
directly against a hand-crafted compliant response, correctly scored 1.0). Remaining honest gap:
StrongREJECT's own protocol uses a strong external judge (GPT-4-class); `phi3-mini-gguf` is still
a small local model, just no longer the same one being graded.

## Phase 5 — Dashboard & writeup (1 week)

- Build the React/TS dashboard: ASR by category, detector confusion matrix, annotated example
  transcripts.
- Write the README: methodology, citations to `04-research-references.md`, and a disclosed-
  limitations section covering both the detection layer's limits and the target agent's own
  design choices (why these three tools, why this memory model).

**Deliverable**: a deployed, clickable dashboard plus a README a recruiter or interviewer can
read end-to-end.

*Shipped and deployed*: **https://vedika-u.github.io/agent-penetration-test/**. `dashboard/`
(React + TS + Vite) builds against the real Phase 3/4 result files (not mock data) — ASR by
category, detector confusion matrix, and the real annotated transcripts including the one
successful attack — and deploys automatically to GitHub Pages via
`.github/workflows/deploy-dashboard.yml` on every push to `master` that touches `dashboard/`.
The disclosed-limitations writeup this phase also calls for (both the detector's and the
benchmark's) is captured in `reports/phase3_detector_eval.md` and `reports/phase4_benchmark.md`
rather than folded into this README directly.

## Estimated total

5-8 weeks at a sustained but non-intensive pace, run in parallel with coursework — matching
the "no imposed deadline" framing in the overview. The added week (vs. reusing OrbitDesk)
comes entirely from Phase 1.
