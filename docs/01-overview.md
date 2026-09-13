# Overview

## Goal

Build a benchmarked tool that probes an LLM-powered agent for prompt-injection and jailbreak
vulnerabilities, scores it against public safety benchmarks, and reports results on a live
dashboard.

## Why this project

Existing portfolio projects (Act Aware, Autonomous Email Productivity Agent, OrbitDesk) share
three gaps this project is designed to close:

1. **No sustained, self-initiated project.** All three existing projects were built under a
   fixed external deadline (two 48-hour hackathons, one internship assignment). This project
   has no imposed deadline and is scoped in phases instead.
2. **No quantified results.** None of the existing projects report a benchmarked metric
   (precision/recall, attack success rate, etc.) — they demo a working pipeline but don't
   measure it against a standard. This project's headline result is a before/after Attack
   Success Rate (ASR) delta, measured against public benchmarks.
3. **No live, clickable artifact.** Act Aware is fully offline and OrbitDesk is local-first;
   neither has something a recruiter can open in a browser. This project ships a dashboard.

## Scope decision: build vs. reuse

Attack generation and jailbreak taxonomies are the product of dedicated research teams —
reimplementing them from scratch would be a multi-year effort and would not demonstrate
anything reimplementing a well-solved problem doesn't already show. Instead:

- **Reuse**: [garak](https://github.com/NVIDIA/garak) (NVIDIA's LLM vulnerability scanner) for
  probe execution; **JailbreakBench** and **StrongREJECT** for evaluation prompts and scoring
  rubrics; deepset's public prompt-injection dataset as a classification baseline.
- **Build**: the harness wiring garak/benchmarks to a target agent, the detection layer, the
  scoring/aggregation pipeline, and the dashboard. This is where the engineering work — and
  the differentiation from a generic "I ran garak" project — actually lives.

## Target agent

The system under test should be a black-box HTTP API in front of an existing agent —
[OrbitDesk](https://github.com/Vedika-u/OrbitDesk-Local-AI-Agent) is the best fit since it's
already local-first, LangGraph-orchestrated, and has an existing verification-node pattern
this project's detection layer can build on.

## Headline deliverable

A results table/dashboard reporting Attack Success Rate (ASR) against JailbreakBench's
curated behaviors and StrongREJECT's rubric, before and after the custom detection layer —
plus a README with methodology and citations, following the same disclosed-limitations
pattern used in OrbitDesk.

## Scope guard

If time-constrained, cut the custom detector (Phase 2 in the roadmap) and rely on garak's
built-in scoring. Phases 1, 3, and 4 (harness + benchmark numbers + dashboard) already exceed
the rigor of the existing three projects on their own. Add the custom detector only for
maximum differentiation.
