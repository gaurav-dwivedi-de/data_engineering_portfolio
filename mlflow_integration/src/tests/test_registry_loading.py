import unittest
from unittest.mock import MagicMock

from registration import (
    ComparisonResult,
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