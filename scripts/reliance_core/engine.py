"""Deterministic packet validation, planning, comparison, evaluation, and rendering.

The engine treats claims, evidence, and model judgements as data. It never
infers facts from prose and never grants authority to execute an action.
"""

from __future__ import annotations

import itertools
import json
import pathlib
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from .schema_validator import load_schema, validate as validate_schema


EVIDENCE_STATES = {"observed", "reconstructed", "inferred", "unavailable", "not_inspected"}
VERIFICATION_STATES = {"not_checked", "supported", "confirmed", "contradicted", "unresolved", "unavailable"}
RELIANCE_STATUSES = {"RELY", "RELY_WITH_CONDITION", "VERIFY", "DO_NOT_RELY", "ABSTAIN"}
BURDEN_LABELS = ["NO_MANUAL_CHECK", "GLANCE", "REVIEW_EVIDENCE", "VERIFY_SOURCE", "HUMAN_JUDGMENT", "HUMAN_ONLY"]
COST_ORDER = {"instant": 0, "<10s": 1, "10-30s": 2, "30-60s": 3, "1-3m": 4, ">3m": 5, "unknown": 6}
COST_SECONDS = {"instant": 0, "<10s": 5, "10-30s": 20, "30-60s": 45, "1-3m": 120, ">3m": 240, "unknown": 10_000}
STATUS_RISK = {"RELY": 4, "RELY_WITH_CONDITION": 3, "VERIFY": 2, "DO_NOT_RELY": 1, "ABSTAIN": 0}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "errors": self.errors, "warnings": self.warnings}


def validate_policy(policy: Mapping[str, Any]) -> ValidationResult:
    """Validate a policy against the root policy schema using the same subset engine."""
    result = ValidationResult()
    if not isinstance(policy, Mapping):
        result.errors.append("policy must be an object")
        return result
    try:
        schema_path = pathlib.Path(__file__).resolve().parents[2] / "schemas" / "policy.schema.json"
        result.errors.extend(validate_schema(policy, load_schema(schema_path), base_dir=schema_path.parent))
    except Exception as exc:
        result.errors.append(f"policy schema validation unavailable: {exc}")
    return result


def _ids(records: Iterable[Mapping[str, Any]], key: str, label: str, result: ValidationResult) -> set[str]:
    seen: set[str] = set()
    for i, record in enumerate(records):
        value = record.get(key)
        if not isinstance(value, str) or not value:
            result.errors.append(f"{label}[{i}] missing non-empty {key}")
            continue
        if value in seen:
            result.errors.append(f"duplicate {label} id: {value}")
        seen.add(value)
    return seen


def _references(values: Any, known: set[str], label: str, result: ValidationResult) -> None:
    if not isinstance(values, list):
        result.errors.append(f"{label} must be an array")
        return
    for value in values:
        if value not in known:
            result.errors.append(f"dangling {label} reference: {value}")


def _find_cycles(dependencies: Mapping[str, Sequence[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, trail: list[str]) -> None:
        if node in visiting:
            try:
                start = trail.index(node)
            except ValueError:
                start = 0
            cycles.append(trail[start:] + [node])
            return
        if node in visited:
            return
        visiting.add(node)
        for dep in dependencies.get(node, []):
            visit(dep, trail + [dep])
        visiting.remove(node)
        visited.add(node)

    for node in dependencies:
        visit(node, [node])
    return cycles


def _contains_authority_key(packet: Mapping[str, Any]) -> list[str]:
    """Find explicit authority grants while leaving raw proposed-action input untouched."""
    forbidden = {"execution_authority", "permission_grant", "authorization_token", "external_action", "autonomous_send"}
    found: list[str] = []
    for key, value in packet.items():
        key_text = str(key).lower()
        if key_text in forbidden or key_text.endswith("_authority"):
            found.append(str(key))
        # An explicit authority/permissions envelope is structural; inspect only
        # its immediate fields. Do not recurse into input, claim text, evidence
        # content, or proposed actions, where words such as "send" are valid data.
        if key_text in {"authority", "permissions", "authorization"} and isinstance(value, Mapping):
            for nested_key in value:
                nested_text = str(nested_key).lower()
                if nested_text in {"execute", "send", "mutate", "mutation", "grant", "can_execute", "can_send"} or nested_text.endswith("_authority"):
                    found.append(f"{key}.{nested_key}")
    return found


def _shape_checks(packet: Mapping[str, Any], result: ValidationResult) -> None:
    required = [
        "schema_version", "run_id", "input", "sources", "claims", "claim_relations", "evidence",
        "assumptions", "contradictions", "failure_modes", "verification_options",
        "minimum_verification_set", "reliance_envelope", "human_verification_burden",
        "residual_uncertainties", "limitations", "recommended_route", "created_at",
    ]
    for key in required:
        if key not in packet:
            result.errors.append(f"missing required field: {key}")
    if packet.get("schema_version") != "0.1":
        result.errors.append("schema_version must be '0.1'")
    if not isinstance(packet.get("input"), Mapping):
        result.errors.append("input must be an object")
    for key in ["sources", "claims", "claim_relations", "evidence", "assumptions", "contradictions", "failure_modes", "verification_options", "residual_uncertainties", "limitations"]:
        if key in packet and not isinstance(packet[key], list):
            result.errors.append(f"{key} must be an array")
    if packet.get("recommended_route") not in {"RELY", "VERIFY_FIRST", "PREPARE_FOR_APPROVAL", "HUMAN_DECISION_REQUIRED", "ABSTAIN"}:
        result.errors.append("recommended_route is invalid")
    record_requirements = {
        "sources": {"source_id", "kind", "locator", "state"},
        "claims": {"claim_id", "text", "type", "materiality", "evidence_ids", "evidence_state", "verification_status", "assumptions", "dependencies", "contradiction_ids", "load_bearing", "reliance_status"},
        "claim_relations": {"relation_id", "from_claim_id", "to_claim_id", "relation"},
        "evidence": {"evidence_id", "source_id", "state", "kind", "locator", "confidence_category", "provenance"},
        "assumptions": {"assumption_id", "affected_claim_ids", "assumption", "why_needed", "evidence_support", "materiality", "verification_method", "status"},
        "contradictions": {"contradiction_id", "claim_ids", "evidence_ids", "description", "status"},
        "failure_modes": {"failure_id", "description", "severity", "affected_claim_ids", "detectable_by", "currently_covered", "residual_risk"},
        "verification_options": {"verification_id", "type", "target_claim_ids", "target_failure_ids", "automated_or_human", "estimated_cost", "evidence_required", "expected_information_gain", "limitations", "available"},
    }
    for collection, required_fields in record_requirements.items():
        values = packet.get(collection, [])
        if not isinstance(values, list):
            continue
        for index, record in enumerate(values):
            if not isinstance(record, Mapping):
                result.errors.append(f"{collection}[{index}] must be an object")
                continue
            missing = sorted(required_fields - set(record))
            if missing:
                result.errors.append(f"{collection}[{index}] missing fields: {', '.join(missing)}")
    for collection in ("minimum_verification_set", "reliance_envelope", "human_verification_burden"):
        if collection in packet and not isinstance(packet[collection], Mapping):
            result.errors.append(f"{collection} must be an object")


def validate_packet(packet: Mapping[str, Any], policy: Mapping[str, Any] | None = None) -> ValidationResult:
    """Validate structure and cross-record invariants of a model packet."""
    result = ValidationResult()
    if not isinstance(packet, Mapping):
        result.errors.append("packet must be an object")
        return result
    try:
        schema_path = pathlib.Path(__file__).resolve().parents[2] / "schemas" / "reliance-packet.schema.json"
        result.errors.extend(validate_schema(packet, load_schema(schema_path), base_dir=schema_path.parent))
    except Exception as exc:  # Schema loading is a project integrity error, not a packet semantic error.
        result.errors.append(f"schema validation unavailable: {exc}")
    active_policy_for_schema = policy or packet.get("policy")
    if isinstance(active_policy_for_schema, Mapping):
        result.errors.extend(validate_policy(active_policy_for_schema).errors)
    _shape_checks(packet, result)
    if _contains_authority_key(packet):
        result.errors.append("execution-authority representation is outside Reliance Compiler scope")

    sources = packet.get("sources", []) if isinstance(packet.get("sources", []), list) else []
    claims = packet.get("claims", []) if isinstance(packet.get("claims", []), list) else []
    evidence = packet.get("evidence", []) if isinstance(packet.get("evidence", []), list) else []
    assumptions = packet.get("assumptions", []) if isinstance(packet.get("assumptions", []), list) else []
    contradictions = packet.get("contradictions", []) if isinstance(packet.get("contradictions", []), list) else []
    failures = packet.get("failure_modes", []) if isinstance(packet.get("failure_modes", []), list) else []
    options = packet.get("verification_options", []) if isinstance(packet.get("verification_options", []), list) else []
    source_ids = _ids(sources, "source_id", "source", result)
    claim_ids = _ids(claims, "claim_id", "claim", result)
    evidence_ids = _ids(evidence, "evidence_id", "evidence", result)
    assumption_ids = _ids(assumptions, "assumption_id", "assumption", result)
    contradiction_ids = _ids(contradictions, "contradiction_id", "contradiction", result)
    failure_ids = _ids(failures, "failure_id", "failure_mode", result)
    option_ids = _ids(options, "verification_id", "verification_option", result)
    relation_ids = _ids(packet.get("claim_relations", []) if isinstance(packet.get("claim_relations", []), list) else [], "relation_id", "claim_relation", result)

    for source in sources:
        if source.get("state") not in EVIDENCE_STATES:
            result.errors.append(f"invalid source state: {source.get('source_id')}")
    for ev in evidence:
        if ev.get("source_id") not in source_ids:
            result.errors.append(f"dangling evidence source_id: {ev.get('evidence_id')}")
        if ev.get("state") not in EVIDENCE_STATES:
            result.errors.append(f"invalid evidence state: {ev.get('evidence_id')}")
        state = ev.get("state")
        content_present = ev.get("content") not in (None, "", [], {})
        description_present = isinstance(ev.get("description"), str) and bool(ev.get("description", "").strip())
        if state in {"unavailable", "not_inspected"}:
            if content_present or description_present:
                result.errors.append(f"semantic content on {state} evidence: {ev.get('evidence_id')}")
        elif state in {"observed", "reconstructed", "inferred"}:
            if content_present == description_present:
                result.errors.append(f"evidence must contain exactly one content or description: {ev.get('evidence_id')}")
            if not ev.get("inspected_at") and not ev.get("inspection_ref"):
                result.errors.append(f"evidence missing inspected_at/inspection_ref: {ev.get('evidence_id')}")
    evidence_by_id = {str(ev.get("evidence_id")): ev for ev in evidence}
    dependencies: dict[str, Sequence[str]] = {}
    for claim in claims:
        cid = claim.get("claim_id")
        deps = claim.get("dependencies", [])
        dependencies[str(cid)] = deps if isinstance(deps, list) else []
        _references(claim.get("evidence_ids", []), evidence_ids, f"claim {cid} evidence", result)
        _references(claim.get("assumptions", []), assumption_ids, f"claim {cid} assumption", result)
        _references(claim.get("dependencies", []), claim_ids, f"claim {cid} dependency", result)
        _references(claim.get("contradiction_ids", []), contradiction_ids, f"claim {cid} contradiction", result)
        linked_unavailable = [evidence_by_id[eid] for eid in claim.get("evidence_ids", []) if eid in evidence_by_id and evidence_by_id[eid].get("state") in {"unavailable", "not_inspected"}]
        if linked_unavailable and claim.get("reliance_status") == "RELY":
            result.errors.append(f"RELY claim references unavailable/not_inspected evidence: {cid}")
        if claim.get("evidence_state") not in EVIDENCE_STATES:
            result.errors.append(f"invalid claim evidence_state: {cid}")
        if claim.get("verification_status") not in VERIFICATION_STATES:
            result.errors.append(f"invalid claim verification_status: {cid}")
        status = claim.get("reliance_status")
        if status not in RELIANCE_STATUSES:
            result.errors.append(f"invalid claim reliance_status: {cid}")
        if status == "RELY_WITH_CONDITION" and not claim.get("conditions"):
            result.errors.append(f"conditionless RELY_WITH_CONDITION: {cid}")
        if status == "RELY" and (claim.get("evidence_state") in {"unavailable", "not_inspected"} or claim.get("verification_status") in {"not_checked", "unresolved", "unavailable", "contradicted"}):
            result.errors.append(f"RELY claim lacks verified support: {cid}")
        if claim.get("load_bearing") and status == "RELY" and not claim.get("evidence_ids"):
            result.errors.append(f"load-bearing RELY claim has no bound evidence: {cid}")
        if claim.get("load_bearing") and status == "RELY":
            bad_assumptions = [a for a in assumptions if (a.get("assumption_id") in claim.get("assumptions", []) or cid in (a.get("affected_claim_ids") or [])) and a.get("status") not in {"supported", "superseded"}]
            if bad_assumptions:
                result.errors.append(f"unsupported load-bearing assumption prevents RELY: {cid}")
            if claim.get("contradiction_ids"):
                open_contras = [c for c in contradictions if c.get("contradiction_id") in claim.get("contradiction_ids", []) and c.get("status") != "resolved"]
                if open_contras:
                    result.errors.append(f"unresolved contradiction prevents RELY: {cid}")
    for cycle in _find_cycles(dependencies):
        result.errors.append("self-dependency/cycle: " + " -> ".join(cycle))

    # Dependency index must agree with explicit relation records.
    relation_deps: dict[str, list[str]] = {cid: [] for cid in claim_ids}
    relations = packet.get("claim_relations", []) if isinstance(packet.get("claim_relations", []), list) else []
    for relation in relations:
        src, dst = relation.get("from_claim_id"), relation.get("to_claim_id")
        if src not in claim_ids or dst not in claim_ids:
            result.errors.append(f"dangling claim relation: {src}->{dst}")
        if relation.get("relation") == "depends_on" and src in claim_ids and dst in claim_ids:
            relation_deps[src].append(dst)
        if src == dst:
            result.errors.append(f"self-dependency relation: {src}")
    for cid in claim_ids:
        if sorted(relation_deps.get(cid, [])) != sorted(dependencies.get(cid, [])):
            if relation_deps.get(cid, []) or dependencies.get(cid, []):
                result.errors.append(f"dependency-index mismatch for claim: {cid}")

    for assumption in assumptions:
        _references(assumption.get("affected_claim_ids", []), claim_ids, f"assumption {assumption.get('assumption_id')} claim", result)
        _references(assumption.get("evidence_support", []), evidence_ids, f"assumption {assumption.get('assumption_id')} evidence", result)
    for contradiction in contradictions:
        _references(contradiction.get("claim_ids", []), claim_ids, f"contradiction {contradiction.get('contradiction_id')} claim", result)
        _references(contradiction.get("evidence_ids", []), evidence_ids, f"contradiction {contradiction.get('contradiction_id')} evidence", result)
        _references(contradiction.get("resolution_evidence_ids", []), evidence_ids, f"contradiction {contradiction.get('contradiction_id')} resolution evidence", result)
        if contradiction.get("status") == "resolved" and not contradiction.get("resolution_evidence_ids"):
            result.errors.append(f"resolved contradiction lacks resolution evidence: {contradiction.get('contradiction_id')}")
    for failure in failures:
        _references(failure.get("affected_claim_ids", []), claim_ids, f"failure {failure.get('failure_id')} claim", result)
        _references(failure.get("detectable_by", []), option_ids, f"failure {failure.get('failure_id')} verifier", result)
    for option in options:
        _references(option.get("target_claim_ids", []), claim_ids, f"verification {option.get('verification_id')} claim", result)
        _references(option.get("target_failure_ids", []), failure_ids, f"verification {option.get('verification_id')} failure", result)
        _references(option.get("evidence_required", []), evidence_ids, f"verification {option.get('verification_id')} evidence", result)
        if option.get("estimated_cost") not in COST_ORDER:
            result.errors.append(f"invalid verification cost: {option.get('verification_id')}")

    minimum = packet.get("minimum_verification_set", {})
    if not isinstance(minimum, Mapping):
        result.errors.append("minimum_verification_set must be an object")
    else:
        selected = minimum.get("selected_verification_ids", [])
        _references(selected, option_ids, "minimum set verification", result)
        _references(minimum.get("covered_failure_ids", []), failure_ids, "minimum set failure", result)
        _references(minimum.get("covered_claim_ids", []), claim_ids, "minimum set claim", result)
        if minimum.get("status") not in {"exact", "heuristic", "policy-constrained", "incomplete"}:
            result.errors.append("minimum set status is invalid")
        if minimum.get("status") == "incomplete" and packet.get("recommended_route") == "RELY":
            result.errors.append("incomplete minimum verification set prohibits RELY")
        selected_options = [o for o in options if o.get("verification_id") in selected]
        unavailable_selected = [o.get("verification_id") for o in selected_options if o.get("available") is False]
        if unavailable_selected:
            result.errors.append("minimum set selects unavailable verification: " + ", ".join(sorted(unavailable_selected)))
        actual_failure = set().union(*(_option_coverage(o)[0] for o in selected_options)) if selected_options else set()
        actual_claim = set().union(*(_option_coverage(o)[1] for o in selected_options)) if selected_options else set()
        declared_failure = set(minimum.get("covered_failure_ids", []) or [])
        declared_claim = set(minimum.get("covered_claim_ids", []) or [])
        if declared_failure != actual_failure:
            result.errors.append("minimum set failure coverage mismatch")
        if declared_claim != actual_claim:
            result.errors.append("minimum set claim coverage mismatch")
        if options:
            for field_name in ("uncovered_failure_ids", "uncovered_claim_ids", "uncovered_verification_types", "selection_method"):
                if field_name not in minimum:
                    result.errors.append(f"minimum set missing deterministic field: {field_name}")

    envelope = packet.get("reliance_envelope", {})
    if isinstance(envelope, Mapping):
        statuses = envelope.get("claim_statuses", {})
        if isinstance(statuses, Mapping):
            for cid, status in statuses.items():
                if cid not in claim_ids:
                    result.errors.append(f"reliance envelope references unknown claim: {cid}")
                elif status != next((c.get("reliance_status") for c in claims if c.get("claim_id") == cid), None):
                    result.errors.append(f"reliance envelope status mismatch: {cid}")
    burden = packet.get("human_verification_burden", {})
    if isinstance(burden, Mapping):
        level, label = burden.get("level"), burden.get("label")
        if not isinstance(level, int) or level < 0 or level > 5 or label not in BURDEN_LABELS or (isinstance(level, int) and label != BURDEN_LABELS[level]):
            result.errors.append("human_verification_burden level/label mismatch")
        if options:
            if "selected_human_verification_ids" not in burden or "effort_band" not in burden:
                result.errors.append("human verification burden missing selected IDs/effort band")
            elif not isinstance(burden.get("selected_human_verification_ids"), list):
                result.errors.append("selected_human_verification_ids must be an array")

    # Claim statuses may not outrun unresolved dependencies.
    by_id = {str(c.get("claim_id")): c for c in claims}
    for claim in claims:
        cid, status = claim.get("claim_id"), claim.get("reliance_status")
        for dep_id in claim.get("dependencies", []) if isinstance(claim.get("dependencies", []), list) else []:
            dep_status = by_id.get(dep_id, {}).get("reliance_status")
            if dep_status in {"DO_NOT_RELY", "ABSTAIN"} and status in {"RELY", "RELY_WITH_CONDITION"}:
                result.errors.append(f"dependency status escalation: {cid} exceeds {dep_id}")
            elif dep_status == "VERIFY" and status == "RELY":
                result.errors.append(f"dependency status escalation: {cid} exceeds {dep_id}")
            elif dep_status == "RELY_WITH_CONDITION" and status == "RELY":
                result.errors.append(f"dependency status escalation: {cid} exceeds {dep_id}")

    active_policy: Mapping[str, Any] | None = policy or packet.get("policy")
    if active_policy:
        _validate_policy_link(packet, active_policy, failures, claims, minimum, burden, result)
    # The primary stored plan is itself a contract: always compare it against
    # deterministic recomputation, not only when an auxiliary stored_plan field
    # happens to be present.
    if isinstance(minimum, Mapping):
        expected_primary = compute_plan(packet)
        if _plan_signature(minimum) != _plan_signature(expected_primary):
            result.errors.append("minimum_verification_set mismatch with deterministic recomputation")
        if isinstance(burden, Mapping) and options:
            selected_human_expected = sorted(o.get("verification_id") for o in options if o.get("automated_or_human") == "human" and o.get("verification_id") in expected_primary.get("selected_verification_ids", []))
            selected_human_declared = sorted(burden.get("selected_human_verification_ids", []) or [])
            if selected_human_declared != selected_human_expected:
                result.errors.append("human verification IDs mismatch with minimum plan")
            if burden.get("effort_band") != expected_primary.get("estimated_human_cost"):
                result.errors.append("human effort band mismatch with minimum plan")
    if isinstance(packet.get("stored_plan"), Mapping):
        expected = compute_plan(packet)
        if _plan_signature(packet["stored_plan"]) != _plan_signature(expected):
            result.errors.append("stored-plan mismatch with deterministic recomputation")
    return result


def _validate_policy_link(packet: Mapping[str, Any], policy: Mapping[str, Any], failures: Sequence[Mapping[str, Any]], claims: Sequence[Mapping[str, Any]], minimum: Mapping[str, Any], burden: Mapping[str, Any], result: ValidationResult) -> None:
    required_claim_names = policy.get("required_claims", [])
    claim_types = {c.get("type") for c in claims}
    claim_ids = {c.get("claim_id") for c in claims}
    for required in required_claim_names if isinstance(required_claim_names, list) else []:
        if required not in claim_ids and required not in claim_types:
            result.errors.append(f"policy required claim not represented: {required}")
    required_failures, required_claims, required_types = _required_targets(packet)
    covered_failures = set(minimum.get("covered_failure_ids", []) if isinstance(minimum.get("covered_failure_ids", []), list) else [])
    covered_claims = set(minimum.get("covered_claim_ids", []) if isinstance(minimum.get("covered_claim_ids", []), list) else [])
    selected_ids = set(minimum.get("selected_verification_ids", []) if isinstance(minimum.get("selected_verification_ids", []), list) else [])
    option_by_id = {o.get("verification_id"): o for o in packet.get("verification_options", []) if isinstance(o, Mapping)}
    selected_types = {option_by_id[oid].get("type") for oid in selected_ids if oid in option_by_id}
    uncovered_types = required_types - selected_types
    if (required_failures - covered_failures or required_claims - covered_claims or uncovered_types) and packet.get("recommended_route") == "RELY":
        result.errors.append("RELY leaves policy-required verification uncovered")
    max_burden = policy.get("max_verification_burden_for_auto_rely")
    if packet.get("recommended_route") == "RELY" and isinstance(max_burden, int) and isinstance(burden.get("level"), int) and burden["level"] > max_burden:
        result.errors.append("auto-rely above policy verification-burden ceiling")


def _required_targets(packet: Mapping[str, Any]) -> tuple[set[str], set[str], set[str]]:
    claims = packet.get("claims", []) if isinstance(packet.get("claims", []), list) else []
    failures = packet.get("failure_modes", []) if isinstance(packet.get("failure_modes", []), list) else []
    policy = packet.get("policy") if isinstance(packet.get("policy"), Mapping) else {}
    required_failure_ids = set(policy.get("required_failure_modes", []) if isinstance(policy.get("required_failure_modes", []), list) else [])
    required_failure_ids |= {f.get("failure_id") for f in failures if f.get("required") or not f.get("currently_covered", False)}
    zero_tolerance = policy.get("zero_tolerance", []) if isinstance(policy.get("zero_tolerance", []), list) else []
    for failure in failures:
        haystack = " ".join(str(failure.get(key, "")).lower() for key in ("failure_id", "description", "severity"))
        if any(str(zero).lower() in haystack for zero in zero_tolerance):
            required_failure_ids.add(failure.get("failure_id"))
    required_claim_ids = {
        c.get("claim_id") for c in claims
        if c.get("load_bearing") and (c.get("reliance_status") != "RELY" or c.get("verification_status") not in {"supported", "confirmed"})
    }
    for wanted in policy.get("required_claims", []) if isinstance(policy.get("required_claims", []), list) else []:
        for claim in claims:
            if claim.get("claim_id") == wanted or claim.get("type") == wanted:
                required_claim_ids.add(claim.get("claim_id"))
    human_review = policy.get("human_review", {}) if isinstance(policy.get("human_review", {}), Mapping) else {}
    if human_review.get("unsupported_material_assumption"):
        unsupported_ids = {a.get("assumption_id") for a in packet.get("assumptions", []) if a.get("status") in {"unsupported", "partially_supported"} and a.get("materiality") in {"medium", "high", "critical"}}
        for claim in claims:
            if unsupported_ids & set(claim.get("assumptions", []) or []):
                required_claim_ids.add(claim.get("claim_id"))
            for assumption in packet.get("assumptions", []):
                if assumption.get("assumption_id") in unsupported_ids and claim.get("claim_id") in set(assumption.get("affected_claim_ids", []) or []):
                    required_claim_ids.add(claim.get("claim_id"))
    required_types = set(policy.get("required_verification_types", []) if isinstance(policy.get("required_verification_types", []), list) else [])
    return {x for x in required_failure_ids if x}, {x for x in required_claim_ids if x}, {x for x in required_types if x}


def _option_coverage(option: Mapping[str, Any]) -> tuple[set[str], set[str]]:
    return set(option.get("target_failure_ids", []) or []), set(option.get("target_claim_ids", []) or [])


def _plan_objective(selected: Sequence[Mapping[str, Any]]) -> tuple[int, int, int, int, tuple[str, ...]]:
    human_costs = [str(o.get("estimated_cost")) for o in selected if o.get("automated_or_human") == "human"]
    unknown_costs = sum(cost == "unknown" for cost in human_costs)
    # Known human cost always outranks an unknown estimate. Within that safety
    # boundary, aggregate conservative band bounds instead of comparing only a
    # single action or the largest band.
    conservative = sum(COST_SECONDS.get(cost, COST_SECONDS["unknown"]) for cost in human_costs)
    human_actions = len(human_costs)
    return unknown_costs, conservative, human_actions, len(selected), tuple(sorted(str(o.get("verification_id")) for o in selected))


def compute_plan(packet: Mapping[str, Any], cap: int = 18) -> dict[str, Any]:
    """Select a bounded minimum verification set over declared mappings only."""
    required_failures, required_claims, required_types = _required_targets(packet)
    options = [o for o in packet.get("verification_options", []) if isinstance(o, Mapping) and o.get("available", True)]
    options.sort(key=lambda o: str(o.get("verification_id", "")))
    candidates: list[tuple[tuple[Any, ...], list[Mapping[str, Any]]]] = []
    status = "exact"
    def satisfies(combo: Sequence[Mapping[str, Any]]) -> bool:
        covered_f = set().union(*(_option_coverage(o)[0] for o in combo)) if combo else set()
        covered_c = set().union(*(_option_coverage(o)[1] for o in combo)) if combo else set()
        covered_types = {o.get("type") for o in combo}
        return required_failures <= covered_f and required_claims <= covered_c and required_types <= covered_types
    if len(options) <= cap:
        # Evaluate every subset up to the cap. Cost, not action count, is the
        # primary objective, so stopping at the first cardinality is unsound.
        for count in range(len(options) + 1):
            for combo in itertools.combinations(options, count):
                if satisfies(combo):
                    candidates.append((_plan_objective(combo), list(combo)))
    else:
        status = "heuristic"
        remaining_f, remaining_c, remaining_types = set(required_failures), set(required_claims), set(required_types)
        chosen: list[Mapping[str, Any]] = []
        while remaining_f or remaining_c or remaining_types:
            viable = []
            for option in options:
                if option in chosen:
                    continue
                f, c = _option_coverage(option)
                gain = len(remaining_f & f) + len(remaining_c & c) + (1 if option.get("type") in remaining_types else 0)
                if gain:
                    viable.append((_plan_objective([option]), -(gain), option))
            if not viable:
                break
            # Human burden is the first greedy criterion; coverage gain breaks
            # ties so obligations still converge whenever possible.
            viable.sort(key=lambda x: (x[0], x[1], str(x[2].get("verification_id", ""))))
            option = viable[0][2]
            chosen.append(option)
            f, c = _option_coverage(option)
            remaining_f -= f
            remaining_c -= c
            remaining_types.discard(option.get("type"))
        candidates = [(_plan_objective(chosen), chosen)]
    if candidates:
        _, selected = min(candidates, key=lambda x: x[0])
    else:
        selected = []
        status = "incomplete"
    covered_f = set().union(*(_option_coverage(o)[0] for o in selected)) if selected else set()
    covered_c = set().union(*(_option_coverage(o)[1] for o in selected)) if selected else set()
    covered_types = {o.get("type") for o in selected}
    if status == "exact" and (packet.get("policy") or packet.get("required_verification_types")):
        status = "policy-constrained"
    human_options = [o for o in selected if o.get("automated_or_human") == "human"]
    total_human_cost = sum(COST_SECONDS.get(str(o.get("estimated_cost")), COST_SECONDS["unknown"]) for o in human_options)
    estimated = "unknown" if any(o.get("estimated_cost") == "unknown" for o in human_options) else _seconds_to_band(total_human_cost)
    uncovered_failures = sorted(required_failures - covered_f)
    uncovered_claims = sorted(required_claims - covered_c)
    uncovered_types = sorted(required_types - covered_types)
    if uncovered_failures or uncovered_claims or uncovered_types:
        status = "incomplete"
    return {
        "selected_verification_ids": sorted(str(o.get("verification_id")) for o in selected),
        "covered_failure_ids": sorted(x for x in covered_f if x in {f.get("failure_id") for f in packet.get("failure_modes", [])}),
        "covered_claim_ids": sorted(x for x in covered_c if x in {c.get("claim_id") for c in packet.get("claims", [])}),
        "uncovered_failure_ids": uncovered_failures,
        "uncovered_claim_ids": uncovered_claims,
        "uncovered_verification_types": uncovered_types,
        "status": status,
        "selection_method": "exhaustive" if len(options) <= cap and selected else ("greedy" if len(options) > cap and selected else "none"),
        "objective": "minimise declared verification cost after required failure/claim coverage",
        "estimated_human_cost": estimated,
        "estimated_human_cost_seconds": total_human_cost,
    }


def _seconds_to_band(seconds: int) -> str:
    if seconds <= 0:
        return "instant"
    if seconds < 10:
        return "<10s"
    if seconds <= 30:
        return "10-30s"
    if seconds <= 60:
        return "30-60s"
    if seconds <= 180:
        return "1-3m"
    return ">3m"


def _plan_signature(plan: Mapping[str, Any]) -> tuple[Any, ...]:
    selected = tuple(sorted(plan.get("selected_verification_ids", []) or []))
    return (
        selected,
        tuple(sorted(plan.get("covered_failure_ids", []) or [])),
        tuple(sorted(plan.get("covered_claim_ids", []) or [])),
        tuple(sorted(plan.get("uncovered_failure_ids", []) or [])),
        tuple(sorted(plan.get("uncovered_claim_ids", []) or [])),
        tuple(sorted(plan.get("uncovered_verification_types", []) or [])),
        plan.get("status"),
        plan.get("selection_method", "none" if not selected else "exhaustive"),
    )


def compare_packets(baseline: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Compare stable packet records and fail closed on identity mismatch."""
    baseline_task = (baseline.get("task_id"), baseline.get("policy_id"), (baseline.get("policy") or {}).get("policy_id") if isinstance(baseline.get("policy"), Mapping) else None)
    candidate_task = (candidate.get("task_id"), candidate.get("policy_id"), (candidate.get("policy") or {}).get("policy_id") if isinstance(candidate.get("policy"), Mapping) else None)
    if baseline_task != candidate_task:
        return {"status": "invalid", "errors": ["task/policy identity mismatch"], "scope": "packet_comparison"}
    base_claim_ids = {c.get("claim_id") for c in baseline.get("claims", [])}
    cand_claim_ids = {c.get("claim_id") for c in candidate.get("claims", [])}
    if base_claim_ids != cand_claim_ids:
        return {"status": "invalid", "errors": ["stable claim-ID mismatch"], "scope": "packet_comparison"}
    base_by = {c.get("claim_id"): c for c in baseline.get("claims", [])}
    cand_by = {c.get("claim_id"): c for c in candidate.get("claims", [])}
    support_changes = []
    for cid in sorted(base_claim_ids):
        before = {"verification_status": base_by[cid].get("verification_status"), "reliance_status": base_by[cid].get("reliance_status")}
        after = {"verification_status": cand_by[cid].get("verification_status"), "reliance_status": cand_by[cid].get("reliance_status")}
        if before != after:
            support_changes.append({"claim_id": cid, "before": before, "after": after})
    base_burden = baseline.get("human_verification_burden", {}).get("level")
    cand_burden = candidate.get("human_verification_burden", {}).get("level")
    burden_regression = isinstance(base_burden, int) and isinstance(cand_burden, int) and cand_burden > base_burden
    base_effort = baseline.get("human_verification_burden", {}).get("effort_band")
    cand_effort = candidate.get("human_verification_burden", {}).get("effort_band")
    base_plan = baseline.get("minimum_verification_set", {})
    cand_plan = candidate.get("minimum_verification_set", {})
    base_f = set(base_plan.get("covered_failure_ids", []) or []) | {f.get("failure_id") for f in baseline.get("failure_modes", []) if f.get("currently_covered")}
    cand_f = set(cand_plan.get("covered_failure_ids", []) or []) | {f.get("failure_id") for f in candidate.get("failure_modes", []) if f.get("currently_covered")}
    unsafe_reliance = []
    for cid in sorted(cand_claim_ids):
        if cand_by[cid].get("reliance_status") == "RELY" and cand_by[cid].get("verification_status") in {"contradicted", "unresolved", "unavailable", "not_checked"}:
            unsafe_reliance.append(cid)
    base_required_f, base_required_c, base_required_t = _required_targets(baseline)
    cand_required_f, cand_required_c, cand_required_t = _required_targets(candidate)
    added_obligations = (cand_required_f - base_required_f) | (cand_required_c - base_required_c) | (cand_required_t - base_required_t)
    new_coverage = (cand_f - base_f) | (set(cand_plan.get("covered_claim_ids", []) or []) - set(base_plan.get("covered_claim_ids", []) or []))
    justified_extra_checks = bool(added_obligations & new_coverage) or bool(added_obligations and len(cand_plan.get("selected_verification_ids", [])) > len(base_plan.get("selected_verification_ids", [])))
    lost_coverage = bool(base_f - cand_f)
    regression = bool(unsafe_reliance) or lost_coverage or ((burden_regression or len(cand_plan.get("selected_verification_ids", [])) > len(base_plan.get("selected_verification_ids", []))) and not justified_extra_checks)
    base_assumptions = {a.get("assumption_id") for a in baseline.get("assumptions", []) if a.get("status") in {"unsupported", "partially_supported"}}
    cand_assumptions = {a.get("assumption_id") for a in candidate.get("assumptions", []) if a.get("status") in {"unsupported", "partially_supported"}}
    base_contradictions = {c.get("contradiction_id") for c in baseline.get("contradictions", []) if c.get("status") != "resolved"}
    cand_contradictions = {c.get("contradiction_id") for c in candidate.get("contradictions", []) if c.get("status") != "resolved"}
    base_abstentions = sorted(c.get("claim_id") for c in baseline.get("claims", []) if c.get("reliance_status") == "ABSTAIN")
    cand_abstentions = sorted(c.get("claim_id") for c in candidate.get("claims", []) if c.get("reliance_status") == "ABSTAIN")
    return {
        "status": "RELIANCE_REGRESSION" if regression else "no_regression",
        "scope": "packet_comparison",
        "burden": {"baseline": base_burden, "candidate": cand_burden, "regression": burden_regression},
        "effort_band": {"baseline": base_effort, "candidate": cand_effort, "regression": COST_ORDER.get(str(cand_effort), 0) > COST_ORDER.get(str(base_effort), 0) if base_effort is not None and cand_effort is not None else False},
        "claim_support_changes": support_changes,
        "unsafe_reliance_claim_ids": unsafe_reliance,
        "unsupported_assumptions": {"baseline": sorted(base_assumptions), "candidate": sorted(cand_assumptions), "added": sorted(cand_assumptions - base_assumptions), "resolved": sorted(base_assumptions - cand_assumptions)},
        "contradictions": {"baseline_open": sorted(base_contradictions), "candidate_open": sorted(cand_contradictions), "added": sorted(cand_contradictions - base_contradictions), "resolved": sorted(base_contradictions - cand_contradictions)},
        "abstention": {"baseline_claim_ids": base_abstentions, "candidate_claim_ids": cand_abstentions},
        "failure_mode_coverage": {"baseline": sorted(base_f), "candidate": sorted(cand_f), "lost": sorted(base_f - cand_f), "gained": sorted(cand_f - base_f)},
        "minimum_verification_set": {"baseline": base_plan, "candidate": cand_plan},
        "recommended_route": {"baseline": baseline.get("recommended_route"), "candidate": candidate.get("recommended_route")},
        "justification": {"added_obligations": sorted(added_obligations), "new_coverage": sorted(new_coverage), "extra_checks_justified": justified_extra_checks, "lost_coverage": sorted(base_f - cand_f)},
    }


def _truth_is_correct(truth: Mapping[str, Any], packet: Mapping[str, Any]) -> bool:
    expected = truth.get("expected_reliance_statuses", {})
    actual = {c.get("claim_id"): c.get("reliance_status") for c in packet.get("claims", [])}
    statuses_match = all(actual.get(cid) == status for cid, status in expected.items())
    expected_safe = truth.get("expected_safe_to_rely")
    if expected_safe is None:
        return statuses_match
    actual_safe = packet.get("recommended_route") == "RELY" and all(status == "RELY" for status in actual.values())
    return statuses_match and actual_safe == bool(expected_safe)


def evaluate_directory(directory: str | pathlib.Path) -> dict[str, Any]:
    """Evaluate fixture records while keeping model packet and evaluator truth separate."""
    root = pathlib.Path(directory)
    records: list[dict[str, Any]] = []
    comparison_records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, Mapping):
            continue
        if "comparison" in data and isinstance(data.get("comparison"), Mapping):
            comparison = data["comparison"]
            if isinstance(comparison.get("baseline"), Mapping) and isinstance(comparison.get("candidate"), Mapping):
                comparison_records.append(compare_packets(comparison["baseline"], comparison["candidate"]))
            continue
        if "model_packet" not in data or "truth" not in data:
            continue
        packet = data["model_packet"]
        truth = data["truth"]
        validation = validate_packet(packet, packet.get("policy") if isinstance(packet, Mapping) else None)
        correct = _truth_is_correct(truth, packet) if validation.valid else False
        selected = set((packet.get("minimum_verification_set") or {}).get("selected_verification_ids", []))
        required_f, _, _ = _required_targets(packet)
        covered_f = set((packet.get("minimum_verification_set") or {}).get("covered_failure_ids", []))
        injected_failures = set(truth.get("injected_failure_ids", []) or [])
        detectors = truth.get("acceptable_detector_ids", {}) if isinstance(truth.get("acceptable_detector_ids", {}), Mapping) else {}
        detected_failures = {failure_id for failure_id in injected_failures if selected & set(detectors.get(failure_id, []) or [])}
        injected_assumptions = set(truth.get("injected_material_assumption_ids", []) or [])
        packet_assumption_ids = {a.get("assumption_id") for a in packet.get("assumptions", [])}
        detected_assumptions = injected_assumptions & packet_assumption_ids
        injected_contradictions = set(truth.get("contradiction_ids", []) or [])
        packet_contradictions = {c.get("contradiction_id") for c in packet.get("contradictions", [])}
        detected_contradictions = injected_contradictions & packet_contradictions
        human_ids = set((packet.get("human_verification_burden") or {}).get("selected_human_verification_ids", []) or [])
        expected_safe = bool(truth.get("expected_safe_to_rely", False))
        actual_unsafe = any(c.get("reliance_status") == "RELY" and c.get("verification_status") in {"contradicted", "unresolved", "unavailable", "not_checked"} for c in packet.get("claims", [])) or (packet.get("recommended_route") == "RELY" and bool(injected_failures - detected_failures))
        burden_level = (packet.get("human_verification_burden") or {}).get("level", 0)
        unnecessary = expected_safe and (packet.get("recommended_route") != "RELY" or bool(human_ids) or burden_level > 0)
        effort_band = (packet.get("human_verification_burden") or {}).get("effort_band", "unknown")
        records.append({
            "case_id": data.get("case_id", path.stem), "category": data.get("category", "uncategorised"),
            "expected_invalid": bool(data.get("expected_invalid", False)),
            "valid": validation.valid, "correct_reliance": correct, "selected_count": len(selected),
            "required_failure_count": len(required_f), "covered_failure_count": len(required_f & covered_f),
            "injected_failure_ids": sorted(injected_failures), "detected_failure_ids": sorted(detected_failures),
            "detected_assumption_count": len(detected_assumptions), "injected_assumption_count": len(injected_assumptions),
            "detected_contradiction_count": len(detected_contradictions), "injected_contradiction_count": len(injected_contradictions),
            "unnecessary_verification": bool(unnecessary), "effort_band": effort_band,
            "counterfactual": bool(data.get("counterfactual", False)), "errors": validation.errors,
            "unsafe_reliance": bool(actual_unsafe) if isinstance(packet, Mapping) else False,
            "counterfactual_detected": bool(injected_failures) and injected_failures <= detected_failures if data.get("counterfactual") else None,
        })
    semantic_records = [record for record in records if not record.get("expected_invalid")]
    total = len(semantic_records)
    accepted = sum(1 for r in semantic_records if r["correct_reliance"])
    unsafe = sum(1 for r in semantic_records if r.get("unsafe_reliance"))
    coverage_num = sum(len(set(r.get("detected_failure_ids", []))) for r in semantic_records)
    coverage_den = sum(len(set(r.get("injected_failure_ids", []))) for r in semantic_records)
    assumption_num = sum(r.get("detected_assumption_count", 0) for r in semantic_records)
    assumption_den = sum(r.get("injected_assumption_count", 0) for r in semantic_records)
    contradiction_num = sum(r.get("detected_contradiction_count", 0) for r in semantic_records)
    contradiction_den = sum(r.get("injected_contradiction_count", 0) for r in semantic_records)
    unnecessary_num = sum(1 for r in semantic_records if r.get("unnecessary_verification"))
    cost_distribution: dict[str, int] = {}
    for record in semantic_records:
        band = record.get("effort_band", "unknown")
        cost_distribution[band] = cost_distribution.get(band, 0) + 1
    categories = sorted({r["category"] for r in records})
    counterfactual_records = [r for r in semantic_records if r.get("counterfactual")]
    counterfactual_detected = sum(1 for r in counterfactual_records if r.get("counterfactual_detected"))
    return {
        "scope": "fixture_suite", "cases": total, "total_fixture_records": len(records), "categories": categories,
        "appropriate_reliance": {"numerator": accepted, "denominator": total},
        "unsafe_reliance": {"numerator": unsafe, "denominator": total},
        "failure_mode_coverage": {"numerator": coverage_num, "denominator": coverage_den},
        "unnecessary_verification": {"numerator": unnecessary_num, "denominator": total},
        "assumption_detection": {"numerator": assumption_num, "denominator": assumption_den},
        "contradiction_detection": {"numerator": contradiction_num, "denominator": contradiction_den},
        "verification_cost_distribution": cost_distribution,
        "counterfactual_detection": {"numerator": counterfactual_detected, "denominator": len(counterfactual_records)},
        "reliance_regression": {"numerator": sum(1 for comparison in comparison_records if comparison.get("status") == "RELIANCE_REGRESSION"), "denominator": len(comparison_records)},
        "contract_negatives": {"cases": sum(1 for record in records if record.get("expected_invalid")), "excluded_from_semantic_metrics": True},
        "records": records,
    }


def render_receipt(packet: Mapping[str, Any]) -> str:
    claims = packet.get("claims", [])
    rely = [c.get("text", c.get("claim_id")) for c in claims if c.get("reliance_status") == "RELY"]
    unsupported = [c.get("text", c.get("claim_id")) for c in claims if c.get("reliance_status") in {"DO_NOT_RELY", "VERIFY", "ABSTAIN"}]
    assumptions = [a.get("assumption") for a in packet.get("assumptions", []) if a.get("status") not in {"supported", "superseded"}]
    contradictions = [c.get("description") for c in packet.get("contradictions", []) if c.get("status") != "resolved"]
    minimum = packet.get("minimum_verification_set", {})
    options = {o.get("verification_id"): o for o in packet.get("verification_options", [])}
    selected = [options[s] for s in minimum.get("selected_verification_ids", []) if s in options]
    burden = packet.get("human_verification_burden", {})
    lines = ["RELIANCE RECEIPT", "", "AI Result", str((packet.get("input") or {}).get("text", (packet.get("input") or {}).get("summary", "(structured AI output)"))), "", "Safe to rely on"]
    lines += [f"✓ {item}" for item in rely] or ["(none)"]
    lines += ["", "Unsupported or still requiring verification"]
    lines += [f"✕ {item}" for item in unsupported] or ["(none)"]
    lines += ["", "Critical assumptions"] + ([f"! {a}" for a in assumptions] or ["None recorded"])
    lines += ["", "Contradictions"] + ([f"! {c}" for c in contradictions] or ["None found in supplied evidence"])
    if selected:
        plan_lines = [f"→ {o.get('type', o.get('verification_id'))} ({o.get('estimated_cost', 'unknown')})" for o in selected]
    elif minimum.get("status") == "incomplete":
        plan_lines = ["Incomplete: no available set covers the required obligations"]
    else:
        plan_lines = ["No policy-required verification"]
    lines += ["", "Minimum verification set"] + plan_lines
    lines += ["", "Human verification required", str(burden.get("label", "UNKNOWN")), "", "Recommended route", str(packet.get("recommended_route", "UNKNOWN"))]
    if packet.get("residual_uncertainties"):
        lines += ["", "Remaining uncertainty"] + [f"? {u}" for u in packet["residual_uncertainties"]]
    lines += ["", "Advisory only: this receipt never authorizes external action."]
    return "\n".join(lines)
