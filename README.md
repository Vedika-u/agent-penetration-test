# AgentPenetrationTest

**A red-teaming harness that attacks an LLM agent you build from scratch — then measures, in
numbers, how often the attacks work.**

Most "AI red-teaming" portfolio projects run a public scanner against someone else's chatbot and
call it a day. This one is different on purpose: the target — a LangGraph-orchestrated assistant
with real tools and persistent memory — is authored end-to-end in this repo, so the attack
surface (prompt injection, tool-output injection, memory poisoning) is fully understood rather
than a black box. The harness then drives [garak](https://github.com/NVIDIA/garak) against it,
scores results against public benchmarks ([JailbreakBench](https://jailbreakbench.github.io/),
[StrongREJECT](https://github.com/alexandrasouly/strongreject)), and reports a before/after
Attack Success Rate (ASR) once the detection layer lands.

## Why this project exists

1. **No black-box target.** The agent under test — its tools, its memory model, its
   orchestration graph — is built here, not borrowed. That's a deliberate scope decision (see
   [`docs/01-overview.md`](docs/01-overview.md)): it costs an extra build phase, but it means
   every attack surface in the results table is one I designed and can explain.
2. **A quantified result, not a demo.** The headline deliverable is an ASR delta — a number,
   before and after a custom detection layer — not "it worked when I tried it."
3. **Memory poisoning as a first-class attack path.** The agent's `notes` tool persists across
   turns in SQLite, so an instruction smuggled into memory in one turn can be acted on in a
   later one — an OWASP LLM Top 10 category most toy agents don't have the state to exhibit.
4. **Build vs. reuse, argued explicitly.** Attack taxonomies and probe libraries are the product
   of dedicated research teams (garak, JailbreakBench, StrongREJECT) — reimplementing them
   would just be slower and worse. The engineering effort goes into the target agent, the
   harness wiring, the detection layer, and the scoring pipeline instead. See
   [`docs/01-overview.md`](docs/01-overview.md#scope-decision-build-vs-reuse).

## Status

| Phase | What it delivers | State |
|---|---|---|
| 1 — Target agent | LangGraph agent, 3 tools, SQLite memory, HTTP API | ✅ Done |
| 2 — Harness | garak → target agent → SQLite attempt log | 🔧 In progress |
| 3 — Detection layer | Grounding check → full injection/memory-integrity detector | ⏳ Planned |
| 4 — Benchmark & scoring | ASR before/after, against JailbreakBench + StrongREJECT | ⏳ Planned |
| 5 — Dashboard | Live results UI | ⏳ Planned |

Full plan with deliverables per phase: [`docs/03-roadmap.md`](docs/03-roadmap.md).

## Architecture

```
Attack Corpus  →  Attack Runner   →  Target Agent (this repo, LangGraph)
(JailbreakBench,   (garak probes)      agent → tools → memory → verify
 StrongREJECT,                         │
 deepset PI set)                       ▼
                                  Detection Layer  →  Scorer  →  Dashboard
                                  (in-graph verify     (ASR,      (React)
                                   node, extended)      P/R)
```

- **Target agent** (`src/target_agent/`) — a LangGraph state graph: `agent` node calls an
  Ollama-hosted LLM and decides to respond or call a tool → `tools` node dispatches to
  `web_search` (indirect-injection surface), `add_note` / `list_notes` / `search_notes`
  (SQLite-backed memory — the memory-poisoning surface), or `calculator` → `verify` node checks
  the final answer's grounding before it's returned. Served over FastAPI so the harness treats
  it as a black box, same as any other target.
- **Harness** (`src/harness/`) — wraps the agent's `/attack` endpoint as a garak REST generator,
  runs garak's probe suite against it, and ingests every `(probe, prompt, output, detector
  score)` row from garak's report into SQLite for downstream scoring.
- **Detection layer / scorer / dashboard** — designed, not yet built; see the roadmap.

Full component breakdown and tech-stack rationale: [`docs/02-architecture.md`](docs/02-architecture.md).

## Quickstart

Requires Python 3.11+, [uv](https://docs.astral.sh/uv/), and [Ollama](https://ollama.com/)
running locally. Full walkthrough with troubleshooting: [`docs/00-setup.md`](docs/00-setup.md).

```bash
git clone https://github.com/Vedika-u/agent-penetration-test.git
cd agent-penetration-test
ollama pull llama3.2
uv sync
cp .env.example .env
uv run pytest                              # run the test suite
uv run python -m target_agent.main         # serve the agent on :8000
uv run python scripts/chat.py              # chat with it from the terminal
uv run python -m harness.run               # run garak's probe suite against it
```

## Repo layout

```
src/target_agent/   LangGraph agent under test: graph, tools, memory, verification, HTTP API
src/harness/         garak wrapper: runs probes against the agent, ingests results to SQLite
scripts/             manual smoke-test CLI (chat with the agent from a terminal)
tests/               unit tests for the graph, tools, API contract, and harness ingestion
fixtures/            deterministic web_search fixtures, so agent behavior is reproducible
docs/                full spec: setup, overview, architecture, roadmap, references
```

## Docs

- [`docs/00-setup.md`](docs/00-setup.md) — detailed setup and troubleshooting
- [`docs/01-overview.md`](docs/01-overview.md) — goal, scope, why this project
- [`docs/02-architecture.md`](docs/02-architecture.md) — system design, tech stack, data flow
- [`docs/03-roadmap.md`](docs/03-roadmap.md) — phased build plan with deliverables
- [`docs/04-research-references.md`](docs/04-research-references.md) — papers, benchmarks, and
  tools this project builds on

## Related work

Draws on lessons from an earlier project thread — SIEM/detection work in
[Act Aware](https://github.com/Vedika-u/aware-security-hub) — applied to the emerging niche of
AI/LLM security evaluation.

## About

Built by **Vedika Utturwar** — agentic AI, backend engineering, and security automation.

[Portfolio](https://vedika.dev) · [GitHub](https://github.com/Vedika-u) ·
[LinkedIn](https://www.linkedin.com/in/vedika-utturwar-b37b75336) ·
[Email](mailto:btbti24094_vedika@banasthali.in)
