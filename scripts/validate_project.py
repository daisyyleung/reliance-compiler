#!/usr/bin/env python3
"""Repository-local integrity validator (standard library only, no network)."""

from __future__ import annotations

import json
import pathlib
import re
import sys
from urllib.parse import unquote

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reliance_core import evaluate_directory, validate_packet  # noqa: E402
from reliance_core.schema_validator import load_schema, validate as validate_schema  # noqa: E402


REQUIRED = [
    "README.md", "LICENSE", "AGENTS.md", "skills/reliance-compiler/SKILL.md",
    "skills/reliance-compiler/agents/openai.yaml", "schemas/reliance-packet.schema.json",
    "schemas/policy.schema.json", "schemas/shadow-audit.schema.json", "scripts/reliance.py",
    "scripts/reliance_core/engine.py", "scripts/validate_project.py", "docs/ARCHITECTURE.md",
    "docs/DEVELOPMENT_PLAN.md", "docs/ROADMAP.md", "docs/DIFFERENTIATION.md",
    "docs/PHASE2_INTERFACE.md", "docs/TRUST_ARCHITECTURE_CHECK_PROPOSAL.md",
    "evals/expected/shadow-audit.json", "evals/expected/policy.json",
]
CATEGORIES = {
    "wrong_date", "wrong_recipient", "wrong_timezone", "missing_attachment", "superseded_instruction",
    "forwarded_text_confusion", "unsupported_exact_time", "contradictory_source", "unsupported_sentiment",
    "stale_source", "authority_restriction", "verifier_unavailable", "evidence_unavailable", "benign_correct",
    "partial_correctness", "multiple_independent_claims", "cascading_dependency_error", "human_judgement_required",
    "high_risk_irreversible", "low_risk_reversible",
}


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            fail(f"missing required file: {relative}", errors)
    for schema in sorted((ROOT / "schemas").glob("*.json")):
        try:
            json.loads(schema.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"invalid JSON schema {schema}: {exc}", errors)
    skill = ROOT / "skills/reliance-compiler/SKILL.md"
    if skill.is_file():
        text = skill.read_text(encoding="utf-8")
        if not text.startswith("---") or "name: reliance-compiler" not in text or "description:" not in text:
            fail("skill frontmatter is incomplete", errors)
        for match in re.findall(r"\]\(([^)]+)\)", text):
            if match.startswith(("http:", "https:", "#")):
                continue
            target = (skill.parent / match).resolve()
            if not target.is_file():
                fail(f"broken skill link: {match}", errors)
    # Verify every local Markdown link across the project, not only skill links.
    for markdown in sorted(ROOT.rglob("*.md")):
        markdown_text = markdown.read_text(encoding="utf-8")
        for match in re.findall(r"\]\(([^)]+)\)", markdown_text):
            target_text = match.split("#", 1)[0].strip()
            if not target_text or target_text.startswith(("http:", "https:", "mailto:")):
                continue
            target = (markdown.parent / unquote(target_text)).resolve()
            if not target.exists():
                fail(f"broken Markdown link: {markdown.relative_to(ROOT)} -> {match}", errors)
    # Verify every skill reference exists and every reference is discoverable.
    refs = sorted((skill.parent / "references").glob("*.md")) if skill.parent.exists() else []
    skill_text = skill.read_text(encoding="utf-8") if skill.is_file() else ""
    for ref in refs:
        if ref.name not in skill_text:
            fail(f"reference not discoverable from SKILL.md: {ref.name}", errors)
    fixture_paths = sorted((ROOT / "evals").rglob("*.json"))
    records = []
    for path in fixture_paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"invalid fixture {path}: {exc}", errors)
            continue
        if not isinstance(data, dict) or "model_packet" not in data or "truth" not in data:
            continue
        records.append(data)
        if data.get("deterministic_validation") is not True:
            fail(f"fixture lacks deterministic_validation=true: {path.name}", errors)
        if data.get("model_judgement_separate") is not True:
            fail(f"fixture lacks model_judgement_separate=true: {path.name}", errors)
        packet = data["model_packet"]
        truth = data.get("truth")
        if not data.get("expected_invalid"):
            if not data.get("raw_input") or not isinstance(data.get("raw_input"), dict):
                fail(f"ordinary fixture lacks non-empty raw_input: {path.name}", errors)
            if not isinstance(packet, dict) or not packet.get("claims"):
                fail(f"ordinary fixture is vacuous (no claims): {path.name}", errors)
            if not (packet.get("evidence") or any(c.get("evidence_state") in {"unavailable", "not_inspected"} for c in packet.get("claims", []) if isinstance(c, dict))):
                fail(f"ordinary fixture lacks evidence or explicit unavailable state: {path.name}", errors)
            if not isinstance(truth, dict):
                fail(f"fixture truth must be an object: {path.name}", errors)
            else:
                for truth_key in ("expected_safe_to_rely", "expected_reliance_statuses", "injected_failure_ids", "acceptable_detector_ids", "injected_material_assumption_ids", "contradiction_ids"):
                    if truth_key not in truth:
                        fail(f"fixture truth missing {truth_key}: {path.name}", errors)
                if not truth.get("expected_reliance_statuses"):
                    fail(f"ordinary fixture truth has no expected claim statuses: {path.name}", errors)
                if data.get("counterfactual") and truth.get("injected_failure_ids") and (not packet.get("failure_modes") or not packet.get("verification_options")):
                    fail(f"counterfactual fixture lacks failure modes/options: {path.name}", errors)
                if data.get("category") == "benign_correct":
                    statuses = [claim.get("reliance_status") for claim in packet.get("claims", [])]
                    burden = packet.get("human_verification_burden", {})
                    if packet.get("recommended_route") != "RELY" or not statuses or any(status != "RELY" for status in statuses) or burden.get("level") != 0 or packet.get("minimum_verification_set", {}).get("selected_verification_ids"):
                        fail(f"benign fixture is not zero-review RELY: {path.name}", errors)
        result = validate_packet(packet, packet.get("policy") if isinstance(packet, dict) else None)
        if not result.valid and not data.get("expected_invalid"):
            fail(f"ordinary fixture packet invalid ({path.name}): {result.errors[:2]}", errors)
        if data.get("expected_invalid") and not data.get("expected_error_contains"):
            fail(f"negative fixture needs expected_error_contains ({path.name})", errors)
    categories = {str(item.get("category")) for item in records}
    if len(records) < 25:
        fail(f"need at least 25 evaluation cases; found {len(records)}", errors)
    missing_categories = sorted(CATEGORIES - categories)
    if missing_categories:
        fail("missing evaluation categories: " + ", ".join(missing_categories), errors)
    negatives = [item for item in records if item.get("expected_invalid")]
    if len(negatives) < 5:
        fail("need at least five structural negative controls", errors)
    for item in negatives:
        packet = item.get("model_packet")
        result = validate_packet(packet, packet.get("policy") if isinstance(packet, dict) else None)
        expected = item.get("expected_error_contains")
        if result.valid or not any(str(expected).lower() in error.lower() for error in result.errors):
            fail(f"negative control did not fail for intended reason: {item.get('case_id')}", errors)
    # Exercise the checked-in contracts against representative packet, policy,
    # and shadow-audit samples through the same supported schema subset.
    schema_dir = ROOT / "schemas"
    samples = [
        (ROOT / "evals/expected/baseline.json", schema_dir / "reliance-packet.schema.json"),
        (ROOT / "evals/expected/shadow-audit.json", schema_dir / "shadow-audit.schema.json"),
        (ROOT / "evals/expected/policy.json", schema_dir / "policy.schema.json"),
    ]
    for sample_path, schema_path in samples:
        try:
            sample_data = json.loads(sample_path.read_text(encoding="utf-8"))
            schema_data = load_schema(schema_path)
            schema_errors = validate_schema(sample_data, schema_data, base_dir=schema_dir)
            if schema_errors:
                fail(f"schema sample invalid ({sample_path.name}): {schema_errors[:2]}", errors)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            fail(f"schema sample unreadable ({sample_path.name}): {exc}", errors)
    evaluation = evaluate_directory(ROOT / "evals/fixtures")
    if evaluation.get("appropriate_reliance", {}).get("denominator", 0) == 0:
        fail("appropriate reliance denominator must be nonzero", errors)
    for metric in ("unsafe_reliance", "unnecessary_verification", "failure_mode_coverage", "counterfactual_detection"):
        if evaluation.get(metric, {}).get("denominator", 0) == 0:
            fail(f"{metric} denominator must be nonzero", errors)
    # Counterfactual detection is derived from selected IDs and evaluator truth,
    # never copied from a fixture boolean.
    by_case = {record.get("case_id"): record for record in evaluation.get("records", [])}
    for item in records:
        if not item.get("counterfactual") or item.get("expected_invalid"):
            continue
        truth = item["truth"]
        selected = set(item["model_packet"].get("minimum_verification_set", {}).get("selected_verification_ids", []))
        detectors = truth.get("acceptable_detector_ids", {})
        expected_detected = bool(truth.get("injected_failure_ids")) and all(selected & set(detectors.get(fid, []) or []) for fid in truth.get("injected_failure_ids", []))
        observed = by_case.get(item.get("case_id"), {}).get("counterfactual_detected")
        if observed != expected_detected:
            fail(f"derived counterfactual result mismatch: {item.get('case_id')}", errors)
    result = {"valid": not errors, "errors": errors, "fixture_count": len(records), "category_count": len(categories), "negative_controls": len(negatives), "semantic_metrics": {key: value for key, value in evaluation.items() if key not in {"records", "categories", "scope", "contract_negatives"}}}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
