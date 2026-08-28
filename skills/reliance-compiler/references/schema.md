# Schema guide

The root JSON schemas are machine authority. From the active project skill,
read `../../schemas/reliance-packet.schema.json` and
`../../schemas/policy.schema.json` before emitting a packet. The mirrored skill
may not have those project files beside it, so the exact v0.1 contract needed
for a structural self-check is summarized here.

Emit one JSON object, not a renamed YAML representation. The required top-level
keys are exactly:

```text
schema_version="0.1"; run_id; input; sources; claims; claim_relations;
evidence; assumptions; contradictions; failure_modes; verification_options;
minimum_verification_set; reliance_envelope; human_verification_burden;
residual_uncertainties; limitations; recommended_route; created_at
```

Optional top-level keys are `task_id`, `policy_id`, `policy`, and `stored_plan`.
No other top-level keys are allowed. In particular, do not add an authority or
permissions envelope: proposed actions may remain raw data inside `input`, but
the packet never represents an authority grant.

Use these exact required nested fields:

| Record | Required fields |
|---|---|
| source | `source_id`, `kind`, `locator`, `state` |
| claim | `claim_id`, `text`, `type`, `materiality`, `evidence_ids`, `evidence_state`, `verification_status`, `assumptions`, `dependencies`, `contradiction_ids`, `load_bearing`, `reliance_status` |
| claim relation | `relation_id`, `from_claim_id`, `to_claim_id`, `relation` |
| evidence | `evidence_id`, `source_id`, `state`, `kind`, `locator`, `confidence_category`, `provenance` |
| assumption | `assumption_id`, `affected_claim_ids`, `assumption`, `why_needed`, `evidence_support`, `materiality`, `verification_method`, `status` |
| contradiction | `contradiction_id`, `claim_ids`, `evidence_ids`, `description`, `status` |
| failure mode | `failure_id`, `description`, `severity`, `affected_claim_ids`, `detectable_by`, `currently_covered`, `residual_risk` |
| verification option | `verification_id`, `type`, `target_claim_ids`, `target_failure_ids`, `automated_or_human`, `estimated_cost`, `evidence_required`, `expected_information_gain`, `limitations`, `available` |
| minimum set | `selected_verification_ids`, `covered_failure_ids`, `covered_claim_ids`, `status`, `objective` |
| envelope | `claim_statuses`, `conditions`, `prohibited_reliance` |
| burden | `level`, `label`, `rationale` |

Whenever verification options exist, also include the deterministic minimum-set
fields `uncovered_failure_ids`, `uncovered_claim_ids`,
`uncovered_verification_types`, `selection_method`, `estimated_human_cost`, and
`estimated_human_cost_seconds`. The burden must then include
`selected_human_verification_ids` and `effort_band`.

Canonical enums:

- evidence/source state: `observed`, `reconstructed`, `inferred`, `unavailable`, `not_inspected`
- verification status: `not_checked`, `supported`, `confirmed`, `contradicted`, `unresolved`, `unavailable`
- reliance status: `RELY`, `RELY_WITH_CONDITION`, `VERIFY`, `DO_NOT_RELY`, `ABSTAIN`
- materiality/severity: `low`, `medium`, `high`, `critical`
- verification modality: `automated`, `human`
- cost: `instant`, `<10s`, `10-30s`, `30-60s`, `1-3m`, `>3m`, `unknown`
- plan status: `exact`, `heuristic`, `policy-constrained`, `incomplete`
- selection method: `exhaustive`, `greedy`, `none`
- burden labels 0–5: `NO_MANUAL_CHECK`, `GLANCE`, `REVIEW_EVIDENCE`, `VERIFY_SOURCE`, `HUMAN_JUDGMENT`, `HUMAN_ONLY`
- route: `RELY`, `VERIFY_FIRST`, `PREPARE_FOR_APPROVAL`, `HUMAN_DECISION_REQUIRED`, `ABSTAIN`

An embedded policy uses the exact keys `policy_id`, `task`,
`required_claims`, `required_failure_modes`, `zero_tolerance`, `human_review`,
and `max_verification_burden_for_auto_rely`; optional keys are
`verification_burden_ceiling`, `required_verification_types`, and `notes`.
Use `human_review.unsupported_material_assumption: true` for the material-
assumption review rule; do not pluralize or rename that key.

References are typed: claim `evidence_ids` point to evidence records, not source
records; `detectable_by` points to verification IDs; verification targets point
to claim/failure IDs; verification `evidence_required` also contains evidence
IDs, never a source type or free-text requirement. When needed future evidence
is absent, create a source and evidence record with `state: unavailable`, no
`content` or `description`, and point `evidence_required` to that evidence ID.
Observed, reconstructed, or inferred evidence contains
exactly one of `content` or `description` and an `inspected_at` or
`inspection_ref`. Unavailable or uninspected evidence carries neither semantic
field. All IDs must be unique and every reference must resolve.

Every claim dependency must have one matching `claim_relations` record whose
`relation` is `depends_on`, whose `from_claim_id` is the dependent claim, and
whose `to_claim_id` is the dependency. The dependency list and these edges must
match exactly. Other `supports` or `contradicts` relations may coexist but do
not satisfy the dependency index.

The minimum set is a deterministic contract: covered IDs must be the exact
union of selected option targets; selected options must be available; and all
uncovered obligations must be explicit. Burden
`selected_human_verification_ids` must exactly equal selected human option IDs,
and burden `effort_band` must equal minimum-set `estimated_human_cost`. Thus an
unavailable human-only route may have burden level 5 `HUMAN_ONLY` while the
selected-plan effort remains `instant` because no human option was selectable.

If the project CLI is available, write the JSON packet to a project-local file
and run `python3 -B scripts/reliance.py validate <packet>` followed by
`python3 -B scripts/reliance.py plan <packet>`. Executable validation is the
only basis for saying the packet is schema-valid; otherwise say only that the
structural self-check was completed.
