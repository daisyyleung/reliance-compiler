# Behavioural evaluation cases

The executable fixtures under the project-root `evals/` keep model-produced
packets beside evaluator-owned truth. Each record labels deterministic
validation separately from model judgement and, where applicable, contains a
counterfactual fault. The suite covers wrong date, recipient, timezone,
attachments, supersession, forwarded text, unsupported exact values,
contradictions, sentiment, stale evidence, authority restrictions, unavailable
verifiers/evidence, benign and partial correctness, dependency cascades,
human judgement, and reversible/irreversible recommendations. Metrics are
fixture-scoped and are not production reliability claims.
