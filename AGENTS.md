# Reliance Compiler project instructions

This project inherits and must follow the active global Codex instructions at
`~/.codex/AGENTS.md`. This file adds the local routing, architecture, and
validation contract for Reliance Compiler.

## Project identity

- Project root: the Git top-level containing this file.
- Source and project knowledge are intentionally co-located here.
- The installable project skill is `skills/reliance-compiler/`.
- The active project skill is authoritative. Its Obsidian mirror is
  `../Skills/_projects/reliance-compiler/reliance-compiler` from the project
  root in Daisy's Obsidian workspace.
- The skill is project-local and must not be installed globally unless Daisy
  explicitly requests global installation.
- Inbox routing is Manual.

## Knowledge routing

1. Read this file and the global instructions.
2. Read `00_system/INDEX.md`.
3. Read only the indexes and authoritative documents routed for the task.
4. Inspect implementation or telemetry only when routed knowledge is
   insufficient or direct evidence is required.

## Architecture boundaries

- The skill owns reusable semantic reasoning: claim atomisation, graphing,
  evidence binding, assumption registration, disconfirmation, failure-mode
  modelling, verification-option design, and claim-level reliance guidance.
- Deterministic Python owns structural validation, bounded verification-set
  selection over declared mappings, comparison, fixture evaluation, and receipt
  rendering. It must not pretend to perform semantic reasoning.
- Evidence acquisition, verification execution, permission enforcement,
  external API actions, durable runtime state, event orchestration, security
  policy, and external mutations remain outside this project.
- Do not duplicate multimedia ingestion, repository review, repository
  cleanliness, or general capability-architecture responsibilities.
- Keep evidence separate from interpretation; preserve contradictions and
  explicit unknowns; never invent numeric confidence or execution authority.
- Unsupported load-bearing claims cannot be `RELY`, and downstream claims
  cannot exceed unresolved load-bearing dependencies.
- Minimize declared human verification cost only after policy obligations are
  covered. Label exact, heuristic, policy-constrained, and incomplete results
  honestly.

## Editing and authority

- `docs/ARCHITECTURE.md` is the single architecture authority.
- Root JSON schemas are the machine-readable contract authority; the skill's
  schema reference is an agent-facing guide.
- Root `evals/` owns executable fixtures and evaluator truth. The skill's eval
  document describes behavioral scenarios without duplicating hidden truth.
- Use Python's standard library for the runtime and tests. Do not install
  dependencies for this project.
- Update the applicable `INDEX.md` whenever project knowledge changes.
- Do not delete, overwrite, clean, or publish content without the exact
  authorization required by the global rules.

## Validation

Run the final integrated validation sequence documented in
`20_protocols/INDEX.md` after the last material change. A passing check proves
only the boundary it exercised. Report fixture metrics as fixture-scoped
evidence, never as production reliability or an SLO guarantee.
