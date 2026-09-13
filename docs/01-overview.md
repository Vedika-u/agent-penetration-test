# Overview

## Goal

Build a benchmarked tool that probes an LLM-powered agent for prompt-injection and jailbreak
vulnerabilities, scores it against public safety benchmarks, and reports results on a live
dashboard.

## Why this project

Existing portfolio projects (Act Aware, Autonomous Email Productivity Agent) share three gaps
this project is designed to close:

1. **No sustained, self-initiated project.** Both existing projects were built under a fixed
   external deadline (a 48-hour hackathon, an internship assignment). This project has no
   imposed deadline and is scoped in phases instead.
2. **No quantified results.** Neither existing project reports a benchmarked metric
   (precision/recall, attack success rate, etc.) — they demo a working pipeline but don't
   measure it against a standard. This project's headline result is a before/after Attack
   Success Rate (ASR) delta, measured against public benchmarks.
3. **No live, clickable artifact.** Act Aware is fully offline and has nothing a recruiter can
   open in a browser. This project ships a dashboard.

It's also, deliberately, the first project in this portfolio where the agent under test is
authored end-to-end here rather than borrowed from another repo — the target agent's design
(tools, memory, orchestration) is as much a demonstration of engineering judgment as the
red-teaming harness built around it.

## Scope decision: build vs. reuse

Attack generation and jailbreak taxonomies are the product of dedicated research teams —
reimplementing them from scratch would be a multi-year effort and would not demonstrate
anything reimplementing a well-solved problem doesn't already show. Instead:

- **Reuse**: [garak](https://github.com/NVIDIA/garak) (NVIDIA's LLM vulnerability scanner) for
  probe execution; **JailbreakBench** and **StrongREJECT** for evaluation prompts and scoring
  rubrics; deepset's public prompt-injection dataset as a classification baseline; LangGraph
  as the orchestration framework for the target agent's control flow.
- **Build**: the target agent itself (tools, memory, prompts, LangGraph graph), the harness
  wiring garak/benchmarks to that agent, the detection layer, the scoring/aggregation
  pipeline, and the dashboard. This is where the engineering work — and the differentiation
  from a generic "I ran garak" project — actually lives. No external agent (OrbitDesk or
  otherwise) is reused as the system under test.

## Target agent

The system under test is a target agent built specifically for this project: a multi-tool
assistant with persistent memory, orchestrated with LangGraph. It needs enough realistic
attack surface to make red-teaming results meaningful, without becoming a project of its own:

- **Tools**: web search, a note/task store, and a calculator — enough to create both direct
  (prompt-level) and indirect (tool-output-level) injection surfaces.
- **Memory**: the note/task store persists across turns (SQLite-backed), so memory
  poisoning — an OWASP LLM Top 10 category — is a first-class attack path, not just prompt
  injection.
- **Orchestration**: a LangGraph state graph (agent → tool call → memory read/write →
  response), with a verification node the detection layer (Phase 3) extends rather than
  bolting on separately.

See `02-architecture.md` for the full design and `03-roadmap.md` Phase 1 for the build plan.

## Headline deliverable

A results table/dashboard reporting Attack Success Rate (ASR) against JailbreakBench's
curated behaviors and StrongREJECT's rubric, before and after the custom detection layer —
plus a README with methodology, citations, and a disclosed-limitations section (what the
target agent does and doesn't defend against, and why).

## Scope guard

If time-constrained:

- Keep the target agent (Phase 1) deliberately minimal — three tools, one memory store, no
  additional features — since every later phase depends on it existing at all.
- Cut the custom detector (Phase 3) and rely on garak's built-in scoring first; add it back
  for differentiation once Phases 1, 2, 4, and 5 (agent + harness + benchmark numbers +
  dashboard) are solid on their own.
