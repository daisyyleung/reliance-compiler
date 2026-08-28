import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reliance_core import validate_packet  # noqa: E402


def packet(**overrides):
    base = {
        "schema_version": "0.1", "run_id": "t", "input": {}, "sources": [], "claims": [],
        "claim_relations": [], "evidence": [], "assumptions": [], "contradictions": [],
        "failure_modes": [], "verification_options": [],
        "minimum_verification_set": {"selected_verification_ids": [], "covered_failure_ids": [], "covered_claim_ids": [], "status": "exact", "objective": "none"},
        "reliance_envelope": {"claim_statuses": {}, "conditions": [], "prohibited_reliance": []},
        "human_verification_burden": {"level": 0, "label": "NO_MANUAL_CHECK", "rationale": "test"},
        "residual_uncertainties": [], "limitations": [], "recommended_route": "ABSTAIN", "created_at": "test",
    }
    base.update(overrides)
    return base


class ValidationTests(unittest.TestCase):
    def test_minimal_packet_validates(self):
        self.assertTrue(validate_packet(packet()).valid)

    def test_duplicate_and_dangling_ids_rejected(self):
        result = validate_packet(packet(sources=[{"source_id": "s", "state": "observed"}, {"source_id": "s", "state": "observed"}], evidence=[{"evidence_id": "e", "source_id": "missing", "state": "observed", "kind": "x", "locator": "x", "confidence_category": "unknown", "provenance": "test"}]))
        self.assertFalse(result.valid)
        self.assertTrue(any("duplicate source" in e for e in result.errors))
        self.assertTrue(any("dangling evidence source" in e for e in result.errors))

    def test_unavailable_evidence_cannot_carry_content(self):
        result = validate_packet(packet(sources=[{"source_id": "s", "state": "unavailable"}], evidence=[{"evidence_id": "e", "source_id": "s", "state": "unavailable", "kind": "message", "locator": "none", "content": "text", "confidence_category": "unknown", "provenance": "test"}]))
        self.assertFalse(result.valid)
        self.assertTrue(any("semantic content" in e for e in result.errors))

    def test_observed_evidence_requires_exact_content_and_inspection(self):
        source = {"source_id": "s", "kind": "message", "locator": "x", "state": "observed"}
        evidence = {"evidence_id": "e", "source_id": "s", "state": "observed", "kind": "message", "locator": "x", "content": "a", "description": "b", "confidence_category": "direct", "provenance": "test"}
        result = validate_packet(packet(sources=[source], evidence=[evidence]))
        self.assertFalse(result.valid)
        self.assertTrue(any("exactly one" in e or "inspected" in e for e in result.errors))

    def test_load_bearing_rely_requires_bound_evidence(self):
        claim = {"claim_id": "c1", "text": "x", "type": "fact", "materiality": "high", "evidence_ids": [], "evidence_state": "observed", "verification_status": "confirmed", "assumptions": [], "dependencies": [], "contradiction_ids": [], "load_bearing": True, "reliance_status": "RELY"}
        result = validate_packet(packet(claims=[claim], reliance_envelope={"claim_statuses": {"c1": "RELY"}, "conditions": [], "prohibited_reliance": []}, recommended_route="RELY"))
        self.assertFalse(result.valid)
        self.assertTrue(any("evidence" in e.lower() for e in result.errors))

    def test_primary_plan_mismatch_and_incomplete_rely_are_rejected(self):
        claim = {"claim_id": "c1", "text": "x", "type": "fact", "materiality": "high", "evidence_ids": [], "evidence_state": "inferred", "verification_status": "unresolved", "assumptions": [], "dependencies": [], "contradiction_ids": [], "load_bearing": True, "reliance_status": "VERIFY"}
        failure = {"failure_id": "f1", "description": "x", "severity": "high", "affected_claim_ids": ["c1"], "detectable_by": ["v1"], "currently_covered": False, "residual_risk": "high", "required": True}
        option = {"verification_id": "v1", "type": "check", "target_claim_ids": ["c1"], "target_failure_ids": ["f1"], "automated_or_human": "automated", "estimated_cost": "instant", "evidence_required": [], "expected_information_gain": "high", "limitations": [], "available": True}
        bad = packet(claims=[claim], failure_modes=[failure], verification_options=[option], recommended_route="RELY", minimum_verification_set={"selected_verification_ids": [], "covered_failure_ids": [], "covered_claim_ids": [], "status": "incomplete", "objective": "none"}, reliance_envelope={"claim_statuses": {"c1": "RELY"}, "conditions": [], "prohibited_reliance": []})
        result = validate_packet(bad)
        self.assertFalse(result.valid)
        self.assertTrue(any("mismatch" in e or "RELY" in e for e in result.errors))

    def test_embedded_policy_is_schema_checked(self):
        bad_policy = {"policy_id": "p", "task": "t", "required_claims": [], "required_failure_modes": [], "zero_tolerance": [], "human_review": {}, "max_verification_burden_for_auto_rely": "not-an-integer"}
        result = validate_packet(packet(policy=bad_policy))
        self.assertFalse(result.valid)
        self.assertTrue(any("maximum" in e or "type" in e for e in result.errors))

    def test_conditionless_rely_with_condition_rejected(self):
        claim = {"claim_id": "c1", "text": "x", "type": "fact", "materiality": "medium", "evidence_ids": [], "evidence_state": "observed", "verification_status": "supported", "assumptions": [], "dependencies": [], "contradiction_ids": [], "load_bearing": False, "reliance_status": "RELY_WITH_CONDITION"}
        result = validate_packet(packet(claims=[claim], reliance_envelope={"claim_statuses": {"c1": "RELY_WITH_CONDITION"}, "conditions": [], "prohibited_reliance": []}))
        self.assertFalse(result.valid)
        self.assertTrue(any("conditionless" in e for e in result.errors))

    def test_execution_authority_rejected(self):
        result = validate_packet(packet(execution_authority={"can_execute": True}))
        self.assertFalse(result.valid)
        self.assertTrue(any("execution-authority" in e for e in result.errors))

    def test_action_language_in_raw_input_is_allowed(self):
        result = validate_packet(packet(input={"proposed_action": {"kind": "send-draft", "recipient": "Lee"}}))
        self.assertTrue(result.valid)


if __name__ == "__main__":
    unittest.main()
