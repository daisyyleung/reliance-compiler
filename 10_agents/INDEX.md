---
title: Reliance Compiler Agent Roles Index
status: active
owner: DaisYY Leung
updated: 2026-08-28
source_of_truth: true
supersedes: []
tags: [reliance-compiler, agents, routing]
---

# Agent roles index

This folder records project-specific roles and boundaries. Runtime agent state,
prompts, and generated reports do not belong here.

## Roles

- Root agent: scope, permissions, integration, final verification, registry,
  and mirror ownership.
- Sol planner: read-only architecture and high-impact trade-off decisions.
- Luna worker: bounded implementation and tests with explicit file ownership.
- Terra reviewer: fresh, read-only behavioral and architecture challenge review.

Nested delegation is disabled unless the root explicitly authorizes it under
the global concurrency limit. No project role may treat a reliance route as
execution authority.
