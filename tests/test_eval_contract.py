import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from reliance_core import evaluate_directory  # noqa: E402


class EvaluationContractTests(unittest.TestCase):
    def test_fixture_suite_keeps_truth_separate_and_has_required_categories(self):
        result = evaluate_directory(ROOT / "evals/fixtures")
        self.assertGreaterEqual(result["cases"], 20)
        self.assertEqual(result["scope"], "fixture_suite")
        self.assertIn("wrong_date", result["categories"])
        self.assertIn("appropriate_reliance", result)
        self.assertEqual(result["contract_negatives"]["cases"], 5)
        self.assertEqual(result["appropriate_reliance"]["denominator"], result["cases"])
        self.assertGreater(result["failure_mode_coverage"]["denominator"], 0)
        self.assertGreater(result["counterfactual_detection"]["denominator"], 0)
        self.assertEqual(result["reliance_regression"]["denominator"], 1)

    def test_counterfactual_detection_is_derived_from_selected_ids(self):
        result = evaluate_directory(ROOT / "evals/fixtures")
        records = {record["case_id"]: record for record in result["records"]}
        self.assertTrue(records["c26_counterfactual_detection"]["counterfactual_detected"])
        self.assertFalse(records["c12_verifier_unavailable"]["counterfactual_detected"])


if __name__ == "__main__":
    unittest.main()
