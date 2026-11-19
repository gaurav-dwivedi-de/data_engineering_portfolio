import unittest

from registration import compare_metrics


DATASET = "weather-validation-v1"
PROTOCOL = "time-aware-holdout-v1"
INCUMBENT = {"mae": 0.400, "rmse": 0.550, "r2": 0.990}


def compare(candidate):
    return compare_metrics(
        candidate,
        INCUMBENT,
        candidate_dataset_id=DATASET,
        incumbent_dataset_id=DATASET,
        candidate_protocol=PROTOCOL,
        incumbent_protocol=PROTOCOL,
    )


class TestComparisonRules(unittest.TestCase):
    def test_accepts_candidate_meeting_all_conditions(self):
        result = compare({"mae": 0.396, "rmse": 0.540, "r2": 0.991})
        self.assertTrue(result.accepted)

    def test_rejects_mae_improvement_below_one_percent(self):
        result = compare({"mae": 0.397, "rmse": 0.540, "r2": 0.991})
        self.assertFalse(result.accepted)

    def test_accepts_exact_one_percent_mae_improvement(self):
        result = compare({"mae": 0.396, "rmse": 0.550, "r2": 0.990})
        self.assertTrue(result.accepted)

    def test_rejects_rmse_increase(self):
        result = compare({"mae": 0.390, "rmse": 0.551, "r2": 0.991})
        self.assertFalse(result.accepted)

    def test_rejects_r2_drop_beyond_tolerance(self):
        result = compare({"mae": 0.390, "rmse": 0.540, "r2": 0.9849})
        self.assertFalse(result.accepted)

    def test_accepts_r2_drop_at_tolerance_boundary(self):
        result = compare({"mae": 0.390, "rmse": 0.540, "r2": 0.985})
        self.assertTrue(result.accepted)

    def test_rejects_different_validation_datasets(self):
        result = compare_metrics(
            {"mae": 0.300, "rmse": 0.400, "r2": 0.995},
            INCUMBENT,
            candidate_dataset_id="new-dataset",
            incumbent_dataset_id=DATASET,
            candidate_protocol=PROTOCOL,
            incumbent_protocol=PROTOCOL,
        )
        self.assertFalse(result.accepted)

    def test_rejects_different_evaluation_protocols(self):
        result = compare_metrics(
            {"mae": 0.300, "rmse": 0.400, "r2": 0.995},
            INCUMBENT,
            candidate_dataset_id=DATASET,
            incumbent_dataset_id=DATASET,
            candidate_protocol="protocol-v2",
            incumbent_protocol=PROTOCOL,
        )
        self.assertFalse(result.accepted)

    def test_rejects_missing_metric(self):
        with self.assertRaises(ValueError):
            compare({"mae": 0.300, "rmse": 0.400})

    def test_rejects_non_finite_metric(self):
        with self.assertRaises(ValueError):
            compare({"mae": float("nan"), "rmse": 0.400, "r2": 0.995})


if __name__ == "__main__":
    unittest.main()