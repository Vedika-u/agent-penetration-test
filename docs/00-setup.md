# Setup

## Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/getting-started/installation/)** — dependency management and
  the runner used throughout this doc (`uv run ...`).
- **[Ollama](https://ollama.com/download)**, running locally with a model pulled. The agent is
  configured for `llama3.2` by default:

  ```bash
  ollama pull llama3.2
  ```

  Ollama runs as a background service after install on most platforms; if `ollama pull` can't
  connect, start it in a separate terminal with `ollama serve`.

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
and `--db_path` to ingest into a different database.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `httpx.ConnectError` / connection refused from the agent | Ollama isn't running — `ollama serve`, or check `OLLAMA_BASE_URL` in `.env`. |
| Agent responds but ignores tools / behaves oddly | Confirm the pulled model matches `OLLAMA_MODEL` in `.env` and supports tool calling. |
| `uv run python -m harness.run` can't reach the agent | Start `target_agent.main` first — the harness calls it over HTTP, it doesn't start it. |
| garak probe run is slow / hits the network | Some garak probes call external services for scoring; start with a small `--spec` (e.g. `probes.promptinject`) before running the full suite. |
