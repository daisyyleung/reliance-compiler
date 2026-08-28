---
title: Reliance Compiler Protocol and Validation Index
status: active
owner: DaisYY Leung
updated: 2026-08-28
source_of_truth: true
supersedes: []
tags: [reliance-compiler, protocols, validation]
---

# Protocol and validation index

This folder contains active workflows and validation gates. One-off output and
benchmark results belong in `50_telemetry/`.

## Current protocols

- Global delegation: `~/.codex/protocols/subagent-delegation.md`
- Editing, deletion safety, evidence assurance, and project-skill mirroring:
  `../AGENTS.md` and `~/.codex/AGENTS.md`

## Final validation sequence

Run from the project root after the last material change:

1. `PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/validate_project.py`
2. `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v`
3. In a validation environment where the external skill-creator validator's
   PyYAML dependency is available, run
   `PYTHONDONTWRITEBYTECODE=1 python3 -B ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/reliance-compiler`.
4. Run CLI validation, plan, render, compare, and evaluate smoke checks from
   the README.
5. Perform a fresh-agent forward test using raw input without evaluator truth.
6. Mirror the complete skill and recursively verify byte identity with
   `../Skills/_projects/reliance-compiler/reliance-compiler` from the project
   root in Daisy's Obsidian workspace.

The validator must prove the final file set, links, schema syntax, fixture
inventory, deterministic/model boundary labels, and key negative controls.
Network access and external mutation are not part of validation.
