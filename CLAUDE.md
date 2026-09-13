# Project instructions

This README and `docs/` are used as a hiring artifact — they must stay accurate as the code
changes, not just at the end of a phase.

## Keep README.md and docs/ in sync with the code

Whenever a change touches `src/`, `scripts/`, `tests/`, `fixtures/`, or `pyproject.toml` in a way
that affects behavior, setup, or structure, check whether `README.md` and the relevant file(s) in
`docs/` need updating, and update them as part of the same change — don't leave it for later.

Concretely:

- New/changed/removed tool, endpoint, or CLI command → `docs/00-setup.md` quickstart, README
  quickstart, and the components section of `docs/02-architecture.md`.
- A roadmap phase completed, started, or re-scoped → README's Status table and
  `docs/03-roadmap.md`.
- New dependency or prerequisite (e.g. a new external service to run locally) →
  `docs/00-setup.md` prerequisites/install steps.
- New top-level file or directory under `src/` → README's Repo layout section.
- A build-vs-reuse or architectural decision (new attack surface, new detector, new benchmark) →
  `docs/01-overview.md` and/or `docs/02-architecture.md`.
- New paper, dataset, or tool the project starts relying on → `docs/04-research-references.md`.

Skip the doc update only when the change genuinely doesn't affect anything a reader of
README/docs would care about — an internal refactor with no behavior change, adding a test for
existing behavior, a typo fix in a code comment. When in doubt, update the docs.

Never advance a phase's status in the README/roadmap ahead of what's actually implemented and
working — the honest "in progress" / "planned" framing is intentional (see the Status table's
own note in README.md) and is more credible to a reviewer than an inflated one.
