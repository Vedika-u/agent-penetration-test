# Architecture

## Data flow

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│ Attack Corpus     │ →  │ Attack Runner     │ →  │ Target Agent        │
│ (JailbreakBench,  │    │ (garak probes +   │    │ (built from scratch │
│ StrongREJECT,      │    │ custom injection   │    │ here: LangGraph,    │
│ deepset PI set)    │    │ payloads)          │    │ tools + memory,     │
│                    │    │                    │    │ run as an HTTP API) │
└─────────────────┘     └──────────────────┘     └──────────┬─────────┘
                                                              │ response
                                                              ▼
                                                   ┌────────────────────┐
                                                   │ Detection Layer     │
                                                   │ - grounding/claim   │
                                                   │   check             │
                                                   │ - embedding-        │
                                                   │   similarity        │
                                                   │   injection detector│
                                                   │ - memory-integrity  │
                                                   │   check             │
                                                   └──────────┬─────────┘
                                                              ▼
                                                   ┌────────────────────┐
                                                   │ Scorer              │
                                                   │ (StrongREJECT-style │
                                                   │ auto-eval: ASR,     │
                                                   │ precision/recall)   │
                                                   └──────────┬─────────┘
                                                              ▼
                                                   ┌────────────────────┐
                                                   │ Dashboard            │
                                                   │ (React/TS)           │
                                                   └────────────────────┘
```

## Components

### Target agent (built from scratch)
The system under test, purpose-built for this project rather than reused from another repo:

- **Orchestration**: a LangGraph state graph — `agent` node (LLM call, decides to respond or
  call a tool) → `tool` node (dispatches to one of the three tools below) → `memory` node
  (reads/writes the persistent store) → back to `agent`, looping until a final response.
- **Tools**:
  - `web_search` — the main indirect-injection surface (attacker content can arrive inside a
    tool result the agent then reasons over).
  - `notes` — a CRUD-style task/note store, backed by SQLite, that persists across turns. This
    is also the **memory-poisoning** surface: a malicious instruction written to a note in one
    turn can be read back and acted on in a later turn.
  - `calculator` — low-risk, included mainly so the agent has a benign tool to fall back to in
    control-condition tests.
- **Verification node**: a graph node that checks tool outputs and memory reads against the
  agent's own claims before they reach the final response — a minimal grounding check on day
  one, extended into the full detection layer in Phase 3 (same graph, not a bolted-on
  service).
- **Interface**: exposed over HTTP so the attack runner treats it as a black box, the same way
  it would treat any other target. Unhandled errors (e.g. Ollama unreachable mid-turn) return a
  clean `502` instead of a leaked stack trace; an optional bearer-token gate (`API_AUTH_TOKEN`,
  unset by default) exists for `/chat`/`/attack` if this were ever exposed beyond localhost.
  `/chat`'s message is length-bounded (`Field(min_length=1, max_length=8000)`, a human-typed
  interactive endpoint); `/attack` deliberately has **no** such bound — an earlier identical bound
  there caused a live 422 that crashed an entire garak sweep partway through (garak treats any
  non-200 response as fatal), discovered running Phase 2 at full scale, not caught in review.
  Deliberately
  **not** rate-limited: this is a red-team *target* meant to receive bursts of automated attack
  traffic from garak/the benchmark harness with no friction — app-level rate limiting would work
  directly against the project's own purpose. A real public deployment would rate-limit at the
  infra layer (reverse proxy/WAF), not in application code that also has to serve legitimate
  high-volume attack runs.

### Attack corpus
Public datasets, not hand-written prompts, so results are reproducible and comparable to
published baselines:
- JailbreakBench — 100 curated policy-violating behaviors + standardized scoring
- StrongREJECT — harmful-prompt dataset with an automated evaluator
- deepset prompt-injection dataset — quick classification baseline

### Attack runner
[garak](https://github.com/NVIDIA/garak) drives the target agent through its probe suite.
The runner is a thin wrapper that:
- Exposes the target agent as an HTTP endpoint garak can call
- Logs every (attack, response) pair with metadata (probe name, category, timestamp)
- Is swappable — the same runner should work against this project's own target agent, the
  email agent, or a third-party model with only a config change

### Detection layer
The part of the project that isn't just "run someone else's tool" (implemented, `src/target_agent/verification.py`
and `src/target_agent/detection/`):
- A grounding/citation check (`check_grounding`) — extends the target agent's own verification
  node rather than a separate service. Flags a final answer that shares no vocabulary with this
  turn's tool output, and separately flags specific unsupported claims (numbers, proper-noun-like
  tokens) asserted in the answer but absent from any tool output used that turn.
- A memory-integrity check (`check_memory_integrity`) specific to the `notes` tool — regex/keyword
  heuristics over content about to be persisted, flagging (never blocking) instruction-override
  patterns and invisible-unicode obfuscation. The flag is stored alongside the note (`flagged`
  column in `memory/db.py`) and surfaced in `list_notes`/`search_notes` output.
- One purpose-built classifier — `InjectionDetector`
  (`src/target_agent/detection/injection_detector.py`): **embedding similarity**, not
  attention-shift, because Ollama's API (the only inference path this agent uses) doesn't expose
  attention weights, so the Attention Tracker-style approach isn't reproducible here (see the
  module's docstring and `04-research-references.md`). Classifies text by max cosine similarity
  (real Ollama `nomic-embed-text` embeddings) against a curated reference set of jailbreak/
  injection templates, thresholded — the threshold is tuned against labeled data, not guessed
  (see Scorer below).
- Wired live into the graph's `verify` node (`graph.py`) — every turn's human message is
  classified, and the result feeds `state["verification"]` alongside the grounding flags, exposed
  on both `/chat` and `/attack`. Not just an offline eval-only module.

### Scorer
- `src/harness/eval_detector.py` measures the injection detector's own precision/recall/F1 against
  a held-out mix of deepset/prompt-injections and JailbreakBench/JBB-Behaviors — see
  `reports/phase3_detector_eval.md` for the methodology, numbers, and caveats.
- `src/harness/run_benchmark.py` computes Attack Success Rate (ASR) per JBB category, before vs.
  after the detection layer, using a StrongREJECT-*lite* LLM-judge rubric (same local model —
  a disclosed limitation, not a hidden one) — see `reports/phase4_benchmark.md`.
- Both write machine-readable results to `data/results/*.json` for the dashboard to read directly.

### Dashboard
- React + TypeScript (Vite), plain CSS — simpler than the Tailwind/Supabase stack originally
  planned; `dashboard/`, built and verified (`npm run build`) against a fixed static-JSON data
  contract rather than a live database, since the underlying data (detector eval, benchmark ASR,
  sample transcripts) is generated by one-off scripts, not a running service that needs live
  querying.
- Shows: ASR by attack category (before/after), detector confusion matrix + precision/recall/F1
  stat tiles, and a filterable list of annotated example transcripts (attack prompt → agent
  response → detector verdict → whether the attack actually succeeded).
- Reads `data/results/{detector_eval,benchmark_asr,transcripts_sample}.json` from
  `dashboard/public/data/` at runtime — copying real result files there (same names) is the only
  step needed to go from placeholder to real data, no code changes.

## Tech stack

| Layer | Choice | Rationale |
|---|---|---|
| Target agent | Python + LangGraph, built from scratch in this repo | Full control over tools/memory/prompts as authored attack surface; no external agent dependency |
| Attack execution | Python + garak | Reuse a maintained, actively-updated probe library |
| Detection layer | Python, extends the target agent's LangGraph graph; embeddings via Ollama `nomic-embed-text` | Keeps verification in-graph rather than a bolted-on service; embedding similarity is the tractable detection method against an Ollama-only inference path (no attention-weight access) |
| Storage | SQLite (`data/attempts.sqlite3`, `data/memory.sqlite3`) + versioned JSON result files (`data/results/`) | Matches the target agent's own notes/memory store; result JSON is simple, diffable, and is exactly what the dashboard/scorer need — no separate DB service to run |
| Dashboard | React + TypeScript (Vite) + plain CSS, static JSON data contract | Simpler than the Tailwind/Supabase stack originally planned — result data is produced by one-off scripts, not a live service, so a static data contract is the right amount of infrastructure |
| Deployment | Static dashboard (Vercel/GitHub Pages) + precomputed result JSON | Keep this reproducible and cheap to host |
