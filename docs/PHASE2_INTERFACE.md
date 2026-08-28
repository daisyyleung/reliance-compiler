---
title: Phase 2 Agent Trust Layer Interface
status: draft
owner: DaisYY Leung
updated: 2026-08-28
source_of_truth: false
supersedes: []
tags: [reliance-compiler, phase2]
---

# Phase 2 interface (design only)

An outer `agent-trust-layer` may consume a validated `reliance_packet` and
policy, expose “What Needs Me?”, enforce authority settings, collect human
review, append a reliance ledger, sample shadow audits, select delegation
levels, and record post-action verification. It must treat `recommended_route`
as advisory, preserve packet IDs, and own all permission/execution/state
boundaries. v0.1 provides no connector or sending implementation.

## Input contract

The consumer accepts `schema_version`, `run_id`, `input`, `sources`, `claims`,
`claim_relations`, `evidence`, `assumptions`, `contradictions`,
`failure_modes`, `verification_options`, `minimum_verification_set`,
`reliance_envelope`, `human_verification_burden`, `residual_uncertainties`,
`limitations`, `recommended_route`, and `created_at` as defined by the root
packet schema. Optional `task_id`, `policy_id`, and embedded `policy` identify
the decision boundary. Every human gate should cite claim IDs and verification
IDs; an approval record is not evidence of correctness.

## Authority boundary

Reliance Compiler may recommend `RELY`, `VERIFY_FIRST`,
`PREPARE_FOR_APPROVAL`, `HUMAN_DECISION_REQUIRED`, or `ABSTAIN`. The outer
layer owns policy enforcement, identity/permission checks, connector calls,
durable state, event orchestration, action execution, and post-action checks.
No field in a packet is an execution token. Phase 2's initial email boundary is
READ, CLASSIFY, DRAFT; autonomous sending is prohibited.
