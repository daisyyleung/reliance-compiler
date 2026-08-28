import json
import pathlib
import unittest
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reliance_core import validate_packet  # noqa: E402


class SchemaTests(unittest.TestCase):
    def test_root_schemas_are_valid_json(self):
        for path in sorted((ROOT / "schemas").glob("*.json")):
            with self.subTest(path=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data["type"], "object")
                self.assertIn("$schema", data)

    def test_packet_schema_lists_critical_fields(self):
        data = json.loads((ROOT / "schemas/reliance-packet.schema.json").read_text(encoding="utf-8"))
        for field in ("claims", "evidence", "assumptions", "failure_modes", "minimum_verification_set", "reliance_envelope"):
            self.assertIn(field, data["required"])

    def test_runtime_rejects_schema_divergence(self):
        packet = {
            "schema_version": "0.1", "run_id": "schema", "input": {}, "sources": [],
            "claims": [{"claim_id": "c1", "text": "x", "type": "fact", "materiality": "not-a-materiality", "evidence_ids": [], "evidence_state": "observed", "verification_status": "supported", "assumptions": [], "dependencies": [], "contradiction_ids": [], "load_bearing": False, "reliance_status": "VERIFY", "unexpected": True}],
            "claim_relations": [], "evidence": [], "assumptions": [], "contradictions": [], "failure_modes": [], "verification_options": [],
            "minimum_verification_set": {"selected_verification_ids": [], "covered_failure_ids": [], "covered_claim_ids": [], "status": "exact", "objective": "none"},
            "reliance_envelope": {"claim_statuses": {"c1": "VERIFY"}, "conditions": [], "prohibited_reliance": []},
            "human_verification_burden": {"level": 0, "label": "NO_MANUAL_CHECK", "rationale": "test"},
            "residual_uncertainties": [], "limitations": [], "recommended_route": "ABSTAIN", "created_at": "test",
        }
        result = validate_packet(packet)
        self.assertFalse(result.valid)
        self.assertTrue(any("additional property" in error or "enum" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
