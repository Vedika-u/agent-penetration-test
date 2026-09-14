# Setup

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — dependency management and
  the runner used throughout this doc (`uv run ...`).
- **[Ollama](https://ollama.com/download)**, running locally with two models pulled: `llama3.2`
  (the target agent's chat model, and the Phase 4 benchmark's judge) and `nomic-embed-text` (the
  Phase 3 detection layer's embedding backend):

  ```bash
  ollama pull llama3.2
  ollama pull nomic-embed-text
  ```

  Ollama runs as a background service after install on most platforms; if `ollama pull` can't
  connect, start it in a separate terminal with `ollama serve`.
- **[Node.js](https://nodejs.org/) 18+ and npm** — only needed for the dashboard (`dashboard/`).

## Install

```bash
git clone https://github.com/Vedika-u/agent-penetration-test.git
cd agent-penetration-test
uv sync
cp .env.example .env
```

`uv sync` installs both the target agent's dependencies and the harness's (including `garak`),
since `pyproject.toml` builds both `src/target_agent` and `src/harness` as one package. `.env`
controls the Ollama model/URL, the SQLite paths, and the API port — defaults work out of the box;
override them if you're running a different model or port.

## Run the tests

```bash
uv run pytest
```

Covers the LangGraph agent, each tool (`calculator`, `notes`, `web_search`), the FastAPI contract,
and the harness's report-ingestion logic. These don't require Ollama to be running — the LLM call
is the one part of the graph exercised only through the live agent, below.

## Run the target agent

```bash
uv run python -m target_agent.main
```

Serves the agent on `http://localhost:8000` (`API_PORT` in `.env`). Two endpoints:

- `POST /chat` — multi-turn, keyed by `session_id`; returns the response plus tool-call and
  verification traces. Used by the interactive CLI below.
- `POST /attack` — single-turn, stateless (fresh thread per call); this is what the harness
  points garak at, so attack attempts never share conversation history with each other.

Chat with it interactively once it's running:

```bash
uv run python scripts/chat.py
```

Try: *"search for langgraph and summarize it"* (exercises `web_search`), *"remember that my
favorite color is blue"* then *"what's my favorite color?"* in the same session (exercises the
`notes` memory store across turns), or *"what's 12 * 7"* (exercises `calculator`).

## Run the red-team harness

With the agent running in one terminal (`uv run python -m target_agent.main`), run garak's probe
suite against it in another:

```bash
uv run python -m harness.run --spec probes.promptinject
```

This points garak at the agent's `/attack` endpoint (config in
`src/harness/configs/rest_generator.json`), runs the probe suite, then ingests every
`(probe, prompt, output, detector score)` row from garak's report into
`data/attempts.sqlite3`. Swap `--spec` for any garak probe selector (`garak --help` for syntax),
and `--db_path` to ingest into a different database. garak logs each attempt twice (once
generated, once scored) under the same UUID — the ingester keeps only the fully-scored copy.

Note: each attempt is one full agent turn against a local model, which can take anywhere from a
few seconds to ~2 minutes depending on tool calls — start with a small `--spec`
(e.g. `probes.dan.AutoDANCached`, 3 prompts) before running a large probe set like the full
`probes.promptinject`.

## Run the detection layer's evaluation (Phase 3)

```bash
uv run python -m harness.eval_detector
```

Measures the embedding-similarity injection detector
(`src/target_agent/detection/injection_detector.py`) against a held-out mix of
deepset/prompt-injections and JailbreakBench/JBB-Behaviors, and writes precision/recall/F1 to
`data/results/detector_eval.json` and `reports/phase3_detector_eval.md`. Downloads are cached
under `data/cache/`. Requires Ollama's `nomic-embed-text` (see Prerequisites).

## Run the Phase 4 benchmark (ASR before/after detection)

```bash
uv run python -m harness.run_benchmark
```

Requires the target agent running (above). Samples behaviors from JailbreakBench/JBB-Behaviors,
attacks the live agent with a few jailbreak-template wrappers, scores compliance with a
StrongREJECT-*lite* LLM-judge rubric, and reports Attack Success Rate before vs. after the
detection layer to `data/results/benchmark_asr.json`, `data/results/transcripts_sample.json`, and
`reports/phase4_benchmark.md` (which also documents this run's scope/caveats — it's a stratified
subset of the full 100 behaviors, not all of them, given local-model runtimes).

## Run the dashboard (Phase 5)

Live at **https://vedika-u.github.io/agent-penetration-test/** — auto-deployed by
`.github/workflows/deploy-dashboard.yml` on every push to `master` that touches `dashboard/`.

To run it locally instead:

```bash
cd dashboard
npm install
npm run dev      # local dev server
npm run build    # static production build (dashboard/dist/)
```

Reads `data/results/{detector_eval,benchmark_asr,transcripts_sample}.json` — copy (or symlink)
those files into `dashboard/public/data/` under the same names before building to show real
results instead of the placeholder fixtures.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `httpx.ConnectError` / connection refused from the agent | Ollama isn't running — `ollama serve`, or check `OLLAMA_BASE_URL` in `.env`. |
| Agent responds but ignores tools / behaves oddly | Confirm the pulled model matches `OLLAMA_MODEL` in `.env` and supports tool calling. |
| `uv run python -m harness.run` can't reach the agent | Start `target_agent.main` first — the harness calls it over HTTP, it doesn't start it. |
| garak probe run is slow / hits the network | Some garak probes call external services for scoring; start with a small `--spec` (e.g. `probes.promptinject`) before running the full suite. |
| `eval_detector` / live `/attack` calls fail with a 404 from Ollama's embeddings endpoint | `nomic-embed-text` isn't pulled — `ollama pull nomic-embed-text`. |
| `run_benchmark` / `eval_detector` fail to download datasets | Needs outbound internet access to `huggingface.co` the first time; results are cached under `data/cache/` afterward. |
| `harness.run` crashes entirely with `requests.exceptions.ReadTimeout` partway through a probe | A single slow multi-tool-call agent turn exceeded `request_timeout` in `configs/rest_generator.json` (default 300s) — garak aborts the whole run rather than skipping one slow attempt. Raise `request_timeout` further if this recurs on slower hardware, or use a smaller `--spec`/`--generations` so fewer attempts are exposed to the tail latency. |
