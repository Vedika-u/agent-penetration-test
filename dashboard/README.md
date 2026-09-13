# Dashboard

Phase 5 of the [agent-red-team](../README.md) project: a React + TypeScript (Vite) app showing
this project's red-teaming results.

## Views

- **ASR by category** — Attack Success Rate before vs. after the detection layer, broken down by
  JailbreakBench behavior category.
- **Detector confusion matrix** — the embedding-similarity injection detector's precision,
  recall, F1, and confusion matrix against held-out labeled data.
- **Annotated transcripts** — a filterable list of individual attack attempts: prompt, the
  target agent's response, whether the detector flagged it, and whether the attack actually
  succeeded. Mismatches (flagged-but-succeeded, flagged-but-benign) are called out, since that's
  the interesting case for a reviewer.

## Data contract

The app fetches three JSON files at runtime from `public/data/`:

- `detector_eval.json` — written by `uv run python -m harness.eval_detector`
- `benchmark_asr.json` and `transcripts_sample.json` — written by
  `uv run python -m harness.run_benchmark`

Shapes are defined in `src/types.ts`. Dropping real result files into `public/data/` under these
same names is the only step needed to update what the dashboard shows — no code changes.

## Run it

```bash
npm install
npm run dev      # local dev server
npm run build    # static production build -> dist/
```
