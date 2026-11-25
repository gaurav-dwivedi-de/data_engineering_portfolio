import unittest
from unittest.mock import MagicMock

from registration import (
    ComparisonResult,
    compare_global_candidate_to_champion,
    get_eligible_production_candidates,
    get_latest_registered_version,
    get_champion_version,
    promote_candidate,
)


class TestRegistryLoading(unittest.TestCase):

    def test_returns_latest_ready_version(self):
        client = MagicMock()

        client.search_model_versions.return_value = [
            MagicMock(version="1", status="READY"),
            MagicMock(version="2", status="READY"),
            MagicMock(version="3", status="PENDING"),
        ]

        result = get_latest_registered_version(
            client,
            "weather-intelligence-sklearn-linear-regression",
        )

        self.assertEqual(result.version, "2")

    def test_rejects_model_without_ready_versions(self):
        client = MagicMock()

        client.search_model_versions.return_value = [
            MagicMock(version="1", status="PENDING"),
        ]

        with self.assertRaises(RuntimeError):
            get_latest_registered_version(
                client,
                "weather-intelligence-sklearn-linear-regression",
            )

    def test_returns_champion_version(self):
        client = MagicMock()
        champion = MagicMock(version="1", status="READY")
        client.get_model_version_by_alias.return_value = champion

        result = get_champion_version(
            client,
            "weather-intelligence-sklearn-linear-regression",
        )

        self.assertEqual(result.version, "1")
        client.get_model_version_by_alias.assert_called_once_with(
            "weather-intelligence-sklearn-linear-regression",
            "champion",
        )

    def test_rejects_missing_champion_alias(self):
        client = MagicMock()
        client.get_model_version_by_alias.side_effect = Exception(
            "Alias not found"
        )

        with self.assertRaises(RuntimeError):
            get_champion_version(
                client,
                "weather-intelligence-sklearn-linear-regression",
            )

    def test_rejects_non_ready_champion(self):
        client = MagicMock()
        client.get_model_version_by_alias.return_value = MagicMock(
            version="2",
            status="PENDING",
        )

        with self.assertRaises(RuntimeError):
            get_champion_version(
                client,
                "weather-intelligence-sklearn-linear-regression",
            )

class TestCandidatePromotion(unittest.TestCase):

    MODEL_NAME = "weather-intelligence-sklearn-linear-regression"

    def setUp(self):
        self.client = MagicMock()

        self.comparison = ComparisonResult(
            accepted=True,
            reasons=("All registration conditions passed",),
            candidate_metrics={"mae": 0.5, "rmse": 0.7, "r2": 0.99},
            incumbent_metrics={"mae": 0.6, "rmse": 0.8, "r2": 0.98},
            mae_improvement=0.1667,
            rmse_change=-0.1,
            r2_change=0.01,
        )

        self.candidate = MagicMock()
        self.candidate.name = self.MODEL_NAME
        self.candidate.version = "2"
        self.candidate.status = "READY"

        self.client.get_model_version.return_value = self.candidate
        self.client.get_model_version_by_alias.return_value = self.candidate

    def test_promotes_accepted_ready_candidate(self):
        result = promote_candidate(
            client=self.client,
            registered_model_name=self.MODEL_NAME,
            version="2",
            comparison=self.comparison,
        )

        self.assertEqual(result.version, "2")

        self.client.set_registered_model_alias.assert_called_once_with(
            name=self.MODEL_NAME,
            alias="champion",
            version="2",
        )

        self.client.get_model_version_by_alias.assert_called_once_with(
            self.MODEL_NAME,
            "champion",
        )

    def test_rejects_candidate_that_failed_comparison(self):
        rejected_comparison = ComparisonResult(
            accepted=False,
            reasons=("MAE improvement below threshold",),
            candidate_metrics={"mae": 0.7, "rmse": 0.9, "r2": 0.95},
            incumbent_metrics={"mae": 0.6, "rmse": 0.8, "r2": 0.98},
            mae_improvement=-0.1667,
            rmse_change=0.1,
            r2_change=-0.03,
        )

        with self.assertRaises(ValueError):
            promote_candidate(
                client=self.client,
                registered_model_name=self.MODEL_NAME,
                version="2",
                comparison=rejected_comparison,
            )

        self.client.set_registered_model_alias.assert_not_called()

    def test_rejects_non_ready_candidate(self):
        self.candidate.status = "PENDING"

        with self.assertRaises(RuntimeError):
            promote_candidate(
                client=self.client,
                registered_model_name=self.MODEL_NAME,
                version="2",
                comparison=self.comparison,
            )

        self.client.set_registered_model_alias.assert_not_called()

    def test_rejects_model_name_mismatch(self):
        self.candidate.name = "unexpected-model"

        with self.assertRaises(RuntimeError):
            promote_candidate(
                client=self.client,
                registered_model_name=self.MODEL_NAME,
                version="2",
                comparison=self.comparison,
            )

        self.client.set_registered_model_alias.assert_not_called()

    def test_rejects_alias_verification_mismatch(self):
        self.client.get_model_version_by_alias.return_value = MagicMock(
            name=self.MODEL_NAME,
            version="1",
            status="READY",
        )

        with self.assertRaises(RuntimeError):
            promote_candidate(
                client=self.client,
                registered_model_name=self.MODEL_NAME,
                version="2",
                comparison=self.comparison,
            )

        self.client.set_registered_model_alias.assert_called_once()

if __name__ == "__main__":
    unittest.main()

class TestGlobalChampionSelection(unittest.TestCase):

    MODEL_NAME = "weather-intelligence-sklearn-linear-regression"
    DATASET_ID = "weather-validation-v1"
    PROTOCOL = "chronological_80_20_boundary_filtered_v1"

    def make_incumbent(self, **overrides):
        tags = {
            "registration_type": "global_production",
            "validation_dataset_id": self.DATASET_ID,
            "evaluation_protocol": self.PROTOCOL,
            "selected_mae": "0.3717",
            "selected_rmse": "0.5084",
            "selected_r2": "0.9928",
        }
        tags.update(overrides)

        incumbent = MagicMock()
        incumbent.status = "READY"
        incumbent.version = "1"
        incumbent.tags = tags
        return incumbent

    def make_candidate(self, **overrides):
        candidate = {
            "model_key": "sklearn_linear_regression",
            "registered_model_name": self.MODEL_NAME,
            "version": "15",
            "run_id": "current-run",
            "validation_dataset_id": self.DATASET_ID,
            "evaluation_protocol": self.PROTOCOL,
            "metrics": {
                "mae": 0.3600,
                "rmse": 0.5000,
                "r2": 0.9930,
            },
        }
        candidate.update(overrides)
        return candidate

    def test_global_comparison_accepts_improved_candidate(self):
        client = MagicMock()
        client.get_model_version_by_alias.return_value = (
            self.make_incumbent()
        )

        result = compare_global_candidate_to_champion(
            client=client,
            selected_candidate=self.make_candidate(),
        )

        self.assertTrue(result.accepted)
        client.set_registered_model_alias.assert_not_called()

    def test_global_comparison_rejects_dataset_mismatch(self):
        client = MagicMock()
        client.get_model_version_by_alias.return_value = (
            self.make_incumbent()
        )

        candidate = self.make_candidate(
            validation_dataset_id="different-dataset"
        )

        result = compare_global_candidate_to_champion(
            client=client,
            selected_candidate=candidate,
        )

        self.assertFalse(result.accepted)
        self.assertTrue(
            any("dataset" in reason.lower() for reason in result.reasons)
        )
        client.set_registered_model_alias.assert_not_called()

    def test_global_comparison_rejects_protocol_mismatch(self):
        client = MagicMock()
        client.get_model_version_by_alias.return_value = (
            self.make_incumbent()
        )

        candidate = self.make_candidate(
            evaluation_protocol="different-protocol"
        )

        result = compare_global_candidate_to_champion(
            client=client,
            selected_candidate=candidate,
        )

        self.assertFalse(result.accepted)
        self.assertTrue(
            any("protocol" in reason.lower() for reason in result.reasons)
        )
        client.set_registered_model_alias.assert_not_called()

    def test_global_comparison_rejects_candidate_below_mae_threshold(self):
        client = MagicMock()
        client.get_model_version_by_alias.return_value = (
            self.make_incumbent()
        )

        candidate = self.make_candidate(
            metrics={
                "mae": 0.3700,
                "rmse": 0.5080,
                "r2": 0.9930,
            }
        )

        result = compare_global_candidate_to_champion(
            client=client,
            selected_candidate=candidate,
        )

        self.assertFalse(result.accepted)
        client.set_registered_model_alias.assert_not_called()

    def test_global_comparison_rejects_non_ready_incumbent(self):
        client = MagicMock()
        incumbent = self.make_incumbent()
        incumbent.status = "PENDING"
        client.get_model_version_by_alias.return_value = incumbent

        with self.assertRaises(RuntimeError):
            compare_global_candidate_to_champion(
                client=client,
                selected_candidate=self.make_candidate(),
            )

        client.set_registered_model_alias.assert_not_called()

    def test_global_comparison_rejects_missing_incumbent_alias(self):
        client = MagicMock()
        client.get_model_version_by_alias.side_effect = Exception(
            "Alias not found"
        )

        with self.assertRaises(RuntimeError):
            compare_global_candidate_to_champion(
                client=client,
                selected_candidate=self.make_candidate(),
            )

        client.set_registered_model_alias.assert_not_called()

    def test_global_comparison_rejects_incumbent_missing_metadata(self):
        client = MagicMock()
        client.get_model_version_by_alias.return_value = (
            self.make_incumbent(selected_mae="")
        )

        with self.assertRaises(RuntimeError):
            compare_global_candidate_to_champion(
                client=client,
                selected_candidate=self.make_candidate(),
            )

        client.set_registered_model_alias.assert_not_called()

    def test_candidate_filter_excludes_previous_evaluation_runs(self):
        client = MagicMock()

        version = MagicMock()
        version.status = "READY"
        version.version = "15"
        version.run_id = "current-run"
        version.source = "models:/candidate-model"

        version.tags = {
            "validation_dataset_id": self.DATASET_ID,
            "evaluation_protocol": self.PROTOCOL,
            "source_evaluation_run_id": "current-run",
        }

        run = MagicMock()
        run.info.status = "FINISHED"
        run.data.tags = {
            "evaluation_type": "candidate_evaluation",
            "registration_eligible": "true",
            "model_key": "sklearn_linear_regression",
            "registered_model_name": self.MODEL_NAME,
            "validation_dataset_id": self.DATASET_ID,
            "evaluation_protocol": self.PROTOCOL,
        }
        run.data.metrics = {
            "candidate_mae": 0.3600,
            "candidate_rmse": 0.5000,
            "candidate_r2": 0.9930,
        }

        client.search_model_versions.side_effect = (
            lambda filter_string: (
                [version]
                if self.MODEL_NAME in filter_string
                else []
            )
        )
        client.get_run.return_value = run

        candidates = get_eligible_production_candidates(
            client=client,
            validation_dataset_id=self.DATASET_ID,
            evaluation_protocol=self.PROTOCOL,
            evaluation_run_ids={"different-run"},
        )

        self.assertEqual(candidates, [])
        client.get_run.assert_not_called()

    def test_candidate_filter_includes_current_evaluation_run(self):
        client = MagicMock()

        version = MagicMock()
        version.status = "READY"
        version.version = "15"
        version.run_id = "current-run"
        version.source = "models:/candidate-model"
        version.tags = {
            "validation_dataset_id": self.DATASET_ID,
            "evaluation_protocol": self.PROTOCOL,
            "source_evaluation_run_id": "current-run",
        }

        run = MagicMock()
        run.info.status = "FINISHED"
        run.data.tags = {
            "evaluation_type": "candidate_evaluation",
            "registration_eligible": "true",
            "model_key": "sklearn_linear_regression",
            "registered_model_name": self.MODEL_NAME,
            "validation_dataset_id": self.DATASET_ID,
            "evaluation_protocol": self.PROTOCOL,
        }
        run.data.metrics = {
            "candidate_mae": 0.3600,
            "candidate_rmse": 0.5000,
            "candidate_r2": 0.9930,
        }

        client.search_model_versions.side_effect = (
            lambda filter_string: (
                [version]
                if self.MODEL_NAME in filter_string
                else []
            )
        )
        client.get_run.return_value = run

        candidates = get_eligible_production_candidates(
            client=client,
            validation_dataset_id=self.DATASET_ID,
            evaluation_protocol=self.PROTOCOL,
            evaluation_run_ids={"current-run"},
        )

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["run_id"], "current-run")
        self.assertEqual(candidates[0]["version"], "15")


if __name__ == "__main__":
    unittest.main()
