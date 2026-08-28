---
title: Reliance Compiler Development Plan
status: active
owner: DaisYY Leung
updated: 2026-08-28
source_of_truth: false
supersedes: []
tags: [reliance-compiler, development]
---

# Development plan

v0.1 is deliberately small: stable packet/policy/audit schemas, an
evidence-disciplined skill, a standard-library validator/planner, a receipt,
comparison, and fixture-scoped evaluation. Build order follows architecture,
schemas, invariants, evaluation design, deterministic runtime, skill guidance,
examples, counterfactuals, and integrated validation.

Validation is local and network-free. Keep model-produced packets and
evaluator-owned truth in separate fields. Any future semantic or acquisition
implementation must be introduced at an explicit outer interface.
