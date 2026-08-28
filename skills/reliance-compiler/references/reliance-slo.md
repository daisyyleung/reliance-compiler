# Reliance SLO design

Describe each capability with explicit fields: `capability`, `task_policy_id`,
`critical_miss_tolerance`, `manual_verification_budget`,
`sampling_requirement`, `regression_trigger`, `measurement_window`, and
`owner`. Link observations to run IDs and claim/failure IDs; retain numerator
and denominator and a scope label. Use ordinal language unless a real baseline
supports a number. v0.1 stores design examples only; it is not a production
SLO service and makes no reliability guarantee or execution authority.
