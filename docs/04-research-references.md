# Research References

Papers, benchmarks, and tools this project builds on. Grouped by how they're used.

## Framing / taxonomy

- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/)
  — the standard vulnerability taxonomy (prompt injection is #1). Use this to frame the
  project's scope in the README.
- [Recent advancements in LLM Red-Teaming: Techniques, Defenses, and Ethical Considerations](https://arxiv.org/pdf/2410.09097)
  — survey paper, good for the literature-review section of the writeup.
- [New prompt injection papers: Agents Rule of Two and The Attacker Moves Second](https://simonwillison.net/2025/Nov/2/new-prompt-injection-papers/)
  — Simon Willison's running log of the newest injection-defense papers; specifically about
  agent tool-use safety, which ties directly to the Act Aware background.

## Target agent design (Phase 1)

- [LangGraph documentation](https://langchain-ai.github.io/langgraph/) — state graph
  orchestration used for the target agent's agent/tool/memory loop.
- OWASP Top 10 for LLM Applications 2025, item on memory/knowledge poisoning — motivates the
  `notes` tool's persistent-memory attack surface and Phase 3's memory-integrity check.

## Detection methods (candidates for Phase 3's custom detector)

- [Attention Tracker: Detecting Prompt Injection Attacks in LLMs](https://aclanthology.org/2025.findings-naacl.123.pdf)
  — detects injection via attention-pattern shifts, no separate classifier needed.
- [PIShield: Detecting Prompt Injection Attacks via Intrinsic LLM Features](https://arxiv.org/pdf/2510.14005)
- [DataSentinel (IEEE S&P 2025)](https://arxiv.org/pdf/2504.19793) — game-theoretic detection
  approach, well-cited.

Pick one of these to actually reproduce (even a simplified version) rather than citing all
three — a working reproduction is worth more than a longer reading list.

## Benchmarks / datasets (for Phase 4's evaluation)

- **JailbreakBench** — open-source benchmark: 100 curated policy-violating behaviors +
  standardized scoring, actively maintained.
- **HarmBench** — standardized red-teaming evaluation framework.
- [StrongREJECT: A StrongREJECT for Empty Jailbreaks](https://arxiv.org/pdf/2402.10260) —
  automated evaluator with human-level agreement; use this for ASR scoring.
- deepset's public prompt-injection dataset — quick classification baseline.

## Tools (reuse, don't reinvent)

- [garak](https://github.com/NVIDIA/garak) — NVIDIA's open-source LLM vulnerability scanner,
  modular probes for injection/jailbreak/leakage/toxicity. Drives Phase 2's attack runner.
- [PyRIT](https://github.com/Azure/PyRIT) — Microsoft's orchestrated, multi-turn red-teaming
  framework (uses an attacker LLM to generate new probes). Consider as a Phase 3+ extension
  once garak's static probes are exhausted.

## Note on scope

Do not attempt to reproduce every paper above. The project's value comes from (1) a working
target agent and harness, (2) one well-measured detector, and (3) real benchmark numbers — not
from breadth of citations. Use this list as a reference to pull from, not a checklist to
complete.
