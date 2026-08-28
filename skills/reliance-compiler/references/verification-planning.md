# Verification planning

Verification options map actionable checks to claims and failure modes and
declare automated/human modality, ordinal cost bands (`instant`, `<10s`,
`10-30s`, `30-60s`, `1-3m`, `>3m`, `unknown`), evidence required,
information-gain category, availability, and limitations. Select the smallest
set that covers policy-required failures and unresolved load-bearing claims.
Exhaustive search is exact only within the declared mapping and cost bands; a
large option set uses deterministic greedy `heuristic`; impossible coverage is
`incomplete` and blocks RELY. Never select an option with `available: false`.
Keep its required failure, claim, or verification-type obligations in the
corresponding `uncovered_*` arrays and use `selection_method: none` when no
available option can be selected. Prefer any sufficient known human-cost plan
over a plan containing an `unknown` human cost; then minimize aggregate human
time, human actions, and total actions in that order.
