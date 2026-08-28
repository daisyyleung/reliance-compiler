# Architecture

Reliance Compiler owns reusable semantic reasoning: claim atomisation,
dependency graphing, evidence binding, assumption registration,
disconfirmation prompts, failure-mode modelling, verification-option design,
and claim-level reliance guidance.

The standard-library control plane owns structural validation, bounded plan
selection over declared mappings, comparison, fixture evaluation, and receipt
rendering. Evidence acquisition, verification execution, permissions, state,
orchestration, security policy, and external mutations remain outside the skill.
