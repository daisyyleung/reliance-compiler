---
title: Reliance Compiler Skill Inventory
status: active
owner: DaisYY Leung
updated: 2026-08-28
source_of_truth: true
supersedes: []
tags: [reliance-compiler, skills, inventory]
---

# Skill inventory

This folder inventories project skills, activation boundaries, dependencies,
and mirrors. It does not contain duplicate packages.

| Skill | Trigger | Authoritative source | Obsidian mirror | Global status |
|---|---|---|---|---|
| `reliance-compiler` | Determine which parts of an AI output are safe to rely on, what remains unsupported, and the minimum policy-sufficient human verification | `../skills/reliance-compiler/` | `../../Skills/_projects/reliance-compiler/reliance-compiler` | Not installed |

The complete skill directory must be mirrored byte-for-byte after every
material edit. Runtime scripts use only Python's standard library and remain an
external deterministic interface rather than hidden semantic reasoning.

Mirror status: synchronized and recursively byte-identical on 2026-08-28.
