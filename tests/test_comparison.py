import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reliance_core import compare_packets, compute_plan, render_receipt  # noqa: E402
from test_validation import packet  # noqa: E402


class ComparisonTests(unittest.TestCase):
    def test_identity_mismatch_fails_closed(self):
        result = compare_packets(packet(task_id="a"), packet(task_id="b"))
        self.assertEqual(result["status"], "invalid")

    def test_burden_regression_is_reported(self):
        baseline = packet(task_id="a", policy_id="p", human_verification_burden={"level": 1, "label": "GLANCE", "rationale": "x"})
        candidate = packet(task_id="a", policy_id="p", human_verification_burden={"level": 3, "label": "VERIFY_SOURCE", "rationale": "x"})
        result = compare_packets(baseline, candidate)
        self.assertEqual(result["status"], "RELIANCE_REGRESSION")
        self.assertTrue(result["burden"]["regression"])

    def test_planner_prefers_automated_lower_cost_option(self):
        p = packet(
            claims=[{"claim_id": "c", "text": "date", "type": "date", "materiality": "high", "evidence_ids": [], "evidence_state": "inferred", "verification_status": "unresolved", "assumptions": [], "dependencies": [], "contradiction_ids": [], "load_bearing": True, "reliance_status": "VERIFY"}],
            failure_modes=[{"failure_id": "f", "description": "wrong date", "severity": "high", "affected_claim_ids": ["c"], "detectable_by": ["v1", "v2"], "currently_covered": False, "residual_risk": "high", "required": True}],
            verification_options=[
                {"verification_id": "v1", "type": "latest-thread", "target_claim_ids": ["c"], "target_failure_ids": ["f"], "automated_or_human": "automated", "estimated_cost": "instant", "evidence_required": [], "expected_information_gain": "high", "limitations": [], "available": True},
                {"verification_id": "v2", "type": "read-source", "target_claim_ids": ["c"], "target_failure_ids": ["f"], "automated_or_human": "human", "estimated_cost": "1-3m", "evidence_required": [], "expected_information_gain": "high", "limitations": [], "available": True},
            ],
        )
        plan = compute_plan(p)
        self.assertEqual(plan["selected_verification_ids"], ["v1"])

    def test_human_cost_precedes_fewer_expensive_actions(self):
        p = packet(
            claims=[{"claim_id": "c", "text": "x", "type": "fact", "materiality": "high", "evidence_ids": [], "evidence_state": "inferred", "verification_status": "unresolved", "assumptions": [], "dependencies": [], "contradiction_ids": [], "load_bearing": True, "reliance_status": "VERIFY"}],
            failure_modes=[
                {"failure_id": "f1", "description": "a", "severity": "high", "affected_claim_ids": ["c"], "detectable_by": ["cheap-a", "expensive"], "currently_covered": False, "residual_risk": "high", "required": True},
                {"failure_id": "f2", "description": "b", "severity": "high", "affected_claim_ids": ["c"], "detectable_by": ["cheap-b", "expensive"], "currently_covered": False, "residual_risk": "high", "required": True},
            ],
            verification_options=[
                {"verification_id": "cheap-a", "type": "a", "target_claim_ids": ["c"], "target_failure_ids": ["f1"], "automated_or_human": "human", "estimated_cost": "<10s", "evidence_required": [], "expected_information_gain": "medium", "limitations": [], "available": True},
                {"verification_id": "cheap-b", "type": "b", "target_claim_ids": ["c"], "target_failure_ids": ["f2"], "automated_or_human": "human", "estimated_cost": "<10s", "evidence_required": [], "expected_information_gain": "medium", "limitations": [], "available": True},
                {"verification_id": "expensive", "type": "expensive", "target_claim_ids": ["c"], "target_failure_ids": ["f1", "f2"], "automated_or_human": "human", "estimated_cost": ">3m", "evidence_required": [], "expected_information_gain": "high", "limitations": [], "available": True},
            ],
        )
        self.assertEqual(compute_plan(p)["selected_verification_ids"], ["cheap-a", "cheap-b"])

    def test_known_human_cost_precedes_unknown_cost(self):
        p = packet(
            claims=[{"claim_id": "c", "text": "x", "type": "fact", "materiality": "high", "evidence_ids": [], "evidence_state": "inferred", "verification_status": "unresolved", "assumptions": [], "dependencies": [], "contradiction_ids": [], "load_bearing": True, "reliance_status": "VERIFY"}],
            failure_modes=[
                {"failure_id": "f1", "description": "a", "severity": "high", "affected_claim_ids": ["c"], "detectable_by": ["known-a", "unknown"], "currently_covered": False, "residual_risk": "high", "required": True},
                {"failure_id": "f2", "description": "b", "severity": "high", "affected_claim_ids": ["c"], "detectable_by": ["known-b", "unknown"], "currently_covered": False, "residual_risk": "high", "required": True},
            ],
            verification_options=[
                {"verification_id": "known-a", "type": "a", "target_claim_ids": ["c"], "target_failure_ids": ["f1"], "automated_or_human": "human", "estimated_cost": ">3m", "evidence_required": [], "expected_information_gain": "medium", "limitations": [], "available": True},
                {"verification_id": "known-b", "type": "b", "target_claim_ids": ["c"], "target_failure_ids": ["f2"], "automated_or_human": "human", "estimated_cost": ">3m", "evidence_required": [], "expected_information_gain": "medium", "limitations": [], "available": True},
                {"verification_id": "unknown", "type": "unknown", "target_claim_ids": ["c"], "target_failure_ids": ["f1", "f2"], "automated_or_human": "human", "estimated_cost": "unknown", "evidence_required": [], "expected_information_gain": "high", "limitations": [], "available": True},
            ],
        )
        plan = compute_plan(p)
        self.assertEqual(plan["selected_verification_ids"], ["known-a", "known-b"])
        self.assertEqual(plan["estimated_human_cost"], ">3m")

    def test_selected_unknown_cost_is_reported_as_unknown(self):
        p = packet(
            claims=[{"claim_id": "c", "text": "x", "type": "fact", "materiality": "high", "evidence_ids": [], "evidence_state": "inferred", "verification_status": "unresolved", "assumptions": [], "dependencies": [], "contradiction_ids": [], "load_bearing": True, "reliance_status": "VERIFY"}],
            failure_modes=[{"failure_id": "f", "description": "a", "severity": "high", "affected_claim_ids": ["c"], "detectable_by": ["unknown"], "currently_covered": False, "residual_risk": "high", "required": True}],
            verification_options=[{"verification_id": "unknown", "type": "unknown", "target_claim_ids": ["c"], "target_failure_ids": ["f"], "automated_or_human": "human", "estimated_cost": "unknown", "evidence_required": [], "expected_information_gain": "high", "limitations": [], "available": True}],
        )
        self.assertEqual(compute_plan(p)["estimated_human_cost"], "unknown")

    def test_required_verification_type_is_honoured(self):
        p = packet(
            policy={"policy_id": "p", "task": "t", "required_claims": [], "required_failure_modes": [], "zero_tolerance": [], "human_review": {}, "max_verification_burden_for_auto_rely": 0, "required_verification_types": ["latest-thread"]},
            verification_options=[{"verification_id": "v", "type": "latest-thread", "target_claim_ids": [], "target_failure_ids": [], "automated_or_human": "automated", "estimated_cost": "instant", "evidence_required": [], "expected_information_gain": "high", "limitations": [], "available": True}],
        )
        self.assertEqual(compute_plan(p)["selected_verification_ids"], ["v"])

    def test_comparison_reports_assumptions_contradictions_and_abstention(self):
        claim = {"claim_id": "c1", "text": "x", "type": "fact", "materiality": "high", "evidence_ids": [], "evidence_state": "inferred", "verification_status": "unresolved", "assumptions": ["a1"], "dependencies": [], "contradiction_ids": ["x1"], "load_bearing": True, "reliance_status": "ABSTAIN"}
        common = packet(task_id="t", policy_id="p", claims=[claim], reliance_envelope={"claim_statuses": {"c1": "ABSTAIN"}, "conditions": [], "prohibited_reliance": []})
        common["assumptions"] = [{"assumption_id": "a1", "affected_claim_ids": ["c1"], "assumption": "x", "why_needed": "x", "evidence_support": [], "materiality": "high", "verification_method": "human", "status": "unsupported"}]
        common["contradictions"] = [{"contradiction_id": "x1", "claim_ids": ["c1"], "evidence_ids": [], "description": "x", "status": "unresolved"}]
        result = compare_packets(common, common)
        self.assertIn("unsupported_assumptions", result)
        self.assertIn("contradictions", result)
        self.assertIn("abstention", result)

    def test_empty_complete_plan_receipt_is_not_incomplete(self):
        receipt = render_receipt(packet())
        self.assertIn("No policy-required verification", receipt)
        self.assertNotIn("manual review remains incomplete", receipt)


if __name__ == "__main__":
    unittest.main()
