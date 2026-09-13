# Architecture

## Data flow

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│ Attack Corpus     │ →  │ Attack Runner     │ →  │ Target Agent        │
│ (JailbreakBench,  │    │ (garak probes +   │    │ (OrbitDesk or email │
│ StrongREJECT,      │    │ custom injection   │    │ agent, run as a     │
│ deepset PI set)    │    │ payloads)          │    │ black-box API)      │
└─────────────────┘     └──────────────────┘     └──────────┬─────────┘
                                                              │ response
                                                              ▼
                                                   ┌────────────────────┐
                                                   │ Detection Layer     │
                                                   │ - grounding check   │
                                                   │ - attention/PI      │
                                                   │   classifier        │
                                                   │ - refusal detector  │
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
- Is swappable — the same runner should work against OrbitDesk, the email agent, or a
  third-party model with only a config change

### Detection layer
The part of the project that isn't just "run someone else's tool":
- A grounding/citation check, reusing OrbitDesk's verification-node pattern
- One purpose-built classifier — an attention-shift or embedding-similarity detector,
  informed by the Attention Tracker / PIShield papers (see `04-research-references.md`) —
  rather than only relying on garak's built-in judge
- Optionally structured as a small LangGraph pipeline (triage → check → verdict), mirroring
  OrbitDesk's existing architecture

### Scorer
- Computes Attack Success Rate (ASR) per probe category, before and after the detection
  layer is applied
- Uses a StrongREJECT-style automated evaluator for scoring, with precision/recall reported
  against a labeled subset for validation

### Dashboard
- React + TypeScript + Tailwind — same stack as the existing portfolio, so the skillset
  transfers directly
- Shows: ASR by attack category, detector confusion matrix, and a handful of annotated
  example transcripts (attack prompt → agent response → verdict)
- Backed by real stored data (SQLite or Supabase/Postgres), not static JSON, so it reads as
  a live tool rather than a rendered report

## Tech stack

| Layer | Choice | Rationale |
|---|---|---|
| Attack execution | Python + garak | Reuse a maintained, actively-updated probe library |
| Detection layer | Python (+ optional LangGraph) | Matches OrbitDesk's existing pattern |
| Target agent | OrbitDesk (LangGraph, local) | Already built, local-first, has a verification node to extend |
| Storage | SQLite (dev) / Supabase Postgres (deployed) | Matches the email agent's existing backend choice |
| Dashboard | React + TypeScript + Tailwind | Matches the portfolio site's stack |
| Deployment | Static dashboard (Vercel/GitHub Pages) + hosted API or precomputed results | Keep this reproducible and cheap to host |
