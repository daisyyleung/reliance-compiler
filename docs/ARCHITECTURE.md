---
title: Reliance Compiler Architecture
status: active
owner: DaisYY Leung
updated: 2026-08-28
source_of_truth: true
supersedes: []
tags: [reliance-compiler, architecture]
---

# Reliance Compiler architecture

## Thesis

AI can generate more work than people can verify. Reliance Compiler compiles
an output into evidence-bound claims, explicit assumptions, plausible failure
modes, and the minimum useful verification. The objective is to minimise human
verification cost subject to residual reliance risk staying within a declared
policy. It is a Human Verification Optimization Layer, not a trust score,
hallucination checker, generic guardrail, or approval framework.

## Boundaries

The skill owns semantic procedure: atomisation, graphing, evidence binding,
assumption registration, disconfirmation prompts, failure-mode modelling,
verification-option design, and claim-level reliance guidance. Evidence
acquisition and execution remain interfaces supplied by an outer runtime.

The standard-library Python control plane owns only deterministic structural
work: packet invariant checks, bounded set selection over declared mappings,
receipt rendering, packet comparison, and fixture evaluation. It does not infer
semantic support, fetch evidence, enforce permissions, persist runtime state,
or mutate external systems.

## Data flow

`AI output → atomise → claim graph → evidence → assumptions → load-bearing
claims → disconfirmation → failure modes → verification options → cost bands →
minimum set → reliance envelope → receipt`.

Evidence is never silently turned into interpretation. Unknown and
contradictory states remain explicit. A downstream claim cannot outrank an
unresolved dependency; unsupported load-bearing claims cannot be `RELY`.

## Minimum verification algorithm

The planner excludes unavailable options and covers policy-required failure
modes plus unresolved/load-bearing claims. Up to a safe option cap it
enumerates subsets and lexicographically minimises known total cost,
conservative cost band, human-action count, total actions, and sorted IDs. Above
the cap it uses deterministic greedy selection and labels the result
`heuristic`; impossible coverage is `incomplete` and prohibits auto-rely.
`exact` therefore means exact only within the declared mappings and ordinal cost
bands, never globally optimal real-world verification.

## Authority and future composition

Root JSON schemas are machine authority. This document is the architecture
authority; the skill's references are agent guidance. Phase 2 `agent-trust-layer`
may consume packets for policy and human-gate workflows, but Reliance Compiler
does not grant execution authority.
