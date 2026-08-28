---
name: reliance-compiler
description: Compile AI outputs into evidence-bound claims, explicit assumptions, failure modes, and the minimum verification needed for safe human reliance; do not use for generic fact checking, execution, or permission enforcement.
metadata:
  short-description: Minimize human verification without weakening safety
---

# Reliance Compiler

Use this skill when a person or agent needs to know which parts of an AI output
can be relied on, which claims and assumptions need checking, or how to reduce
manual review while preserving policy safety. Produce a claim-level reliance
packet, never a single confidence score.

## Required workflow

Atomise independently falsifiable claims, build a dependency graph, bind only
supplied evidence, register assumptions, mark load-bearing claims, search for
disconfirmation, model failure modes, design verification options, estimate
ordinal human cost, select a bounded minimum verification set, and emit a
reliance envelope plus receipt. Preserve unknowns and contradictions.

Before composing the result, read the schema guide and, when working from the
project source, the root packet and policy JSON schemas it identifies. Emit the
machine packet as JSON using the exact canonical field names and enum values;
do not substitute friendly aliases, YAML-only labels, or prose for required
objects. Include required arrays even when empty. If the companion CLI is
available, validate the packet and replace its declared plan with the CLI's
recomputed plan before rendering the receipt. Otherwise perform the schema
guide's structural self-check and state that executable validation was not run.

`RELY` is prohibited for unsupported load-bearing claims, unresolved
contradictions, unavailable evidence, or unresolved dependencies. A route is
advisory and never grants execution authority or permission to mutate systems.
Do not select an unavailable verification option; leave its obligations
uncovered, mark the plan `incomplete`, and fail closed.

## Progressive disclosure

- Start with [architecture](references/architecture.md) for boundaries and the
  [schema guide](references/schema.md) for packet fields.
- For evidence binding read [evidence contract](references/evidence-contract.md)
  and [claim graph](references/claim-graph.md).
- When assumptions or contradictions matter, read
  [assumption register](references/assumption-register.md) and
  [disconfirmation policy](references/disconfirmation-policy.md).
- For consequential output read [failure-mode model](references/failure-mode-model.md),
  [verification planning](references/verification-planning.md), and
  [reliance envelope](references/reliance-envelope.md).
- Apply policy and SLO guidance from [reliance policy](references/reliance-policy.md)
  and [reliance SLO](references/reliance-slo.md).
- Behavioural scenarios are in [evaluation cases](evals/test-cases.md).

The deterministic companion CLI validates structure, recomputes declared
verification plans, renders receipts, compares packets, and evaluates fixture
truth. It must not invent evidence or semantic judgements.
