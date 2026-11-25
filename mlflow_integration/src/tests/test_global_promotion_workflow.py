import os
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("S3_BUCKET_NAME", "test-weather-bucket")
os.environ.setdefault("AWS_REGION", "eu-west-2")

from mlflow_integration.src import evaluate_models as em


class TestGlobalPromotionWorkflow(unittest.TestCase):

    def setUp(self):
        self.run_ids = [
            "evaluation-run-1",
            "evaluation-run-2",
            "evaluation-run-3",
            "evaluation-run-4",
        ]

        self.dataset_id = "sha256:test-dataset"
        self.protocol = "chronological_80_20_boundary_filtered_v1"

        self.selected = {
            "registered_model_name": "weather-intelligence-sklearn-linear-regression",
            "version": "5",
            "run_id": self.run_ids[0],
            "validation_dataset_id": self.dataset_id,
            "evaluation_protocol": self.protocol,
            "metrics": {
                "mae": 0.30,
                "rmse": 0.45,
                "r2": 0.995,
            },
        }

        self.registered_versions = {
            "sklearn_linear_regression": {
                "registered_model_name": self.selected["registered_model_name"],
                "version": "5",
                "status": "READY",
            }
        }

        self.client = MagicMock()

        evaluation_run = SimpleNamespace(
            data=SimpleNamespace(
                tags={
                    "validation_dataset_id": self.dataset_id,
                    "evaluation_protocol": self.protocol,
                }
            )
        )

        self.client.get_run.side_effect = [
            evaluation_run,
            evaluation_run,
            evaluation_run,
            evaluation_run,
        ]

        self.client.get_model_version.return_value = SimpleNamespace(
            version="2",
            status="READY",
        )

        self.comparison = MagicMock()
        self.comparison.accepted = True
        self.comparison.to_dict.return_value = {
            "accepted": True,
            "reasons": ["Candidate meets promotion policy"],
        }

        self.global_version = SimpleNamespace(version="2")
        self.promoted_version = SimpleNamespace(version="2")

        self.feature_data = em.pd.DataFrame(
            [[1.0] * len(em.FEATURE_COLUMNS) for _ in range(5)],
            columns=em.FEATURE_COLUMNS,
        )

        self.stack = ExitStack()
        self.addCleanup(self.stack.close)

        self.mock_client = self.stack.enter_context(
            patch.object(em, "MlflowClient", return_value=self.client)
        )
        self.mock_tracking_uri = self.stack.enter_context(
            patch.object(em.mlflow, "set_tracking_uri")
        )
        self.mock_select = self.stack.enter_context(
            patch.object(
                em,
                "select_global_champion",
                return_value=self.selected,
            )
        )
        self.mock_compare = self.stack.enter_context(
            patch.object(
                em,
                "compare_global_candidate_to_champion",
                return_value=self.comparison,
            )
        )
        self.mock_register = self.stack.enter_context(
            patch.object(
                em,
                "register_global_champion",
                return_value=self.global_version,
            )
        )
        self.mock_read_parquet = self.stack.enter_context(
            patch.object(
                em.pd,
                "read_parquet",
                return_value=self.feature_data,
            )
        )
        self.mock_validate = self.stack.enter_context(
            patch.object(
                em,
                "validate_global_model_version",
                return_value={"valid": True},
            )
        )
        self.mock_promote = self.stack.enter_context(
            patch.object(
                em,
                "promote_global_champion",
                return_value=self.promoted_version,
            )
        )

    def run_workflow(self):
        return em.promote_global_champion_if_better(
            evaluation_run_ids=self.run_ids,
            registered_versions=self.registered_versions,
        )

    def test_rejected_comparison_does_not_register_or_promote(self):
        self.comparison.accepted = False

        result = self.run_workflow()

        self.assertEqual(result["status"], "NOT_PROMOTED")
        self.mock_register.assert_not_called()
        self.mock_validate.assert_not_called()
        self.mock_promote.assert_not_called()

    def test_candidate_outside_current_batch_aborts_workflow(self):
        self.selected["version"] = "99"

        with self.assertRaisesRegex(
            RuntimeError,
            "does not match a family version",
        ):
            self.run_workflow()

        self.mock_compare.assert_not_called()
        self.mock_register.assert_not_called()
        self.mock_promote.assert_not_called()

    def test_non_ready_global_version_is_not_promoted(self):
        self.client.get_model_version.return_value = SimpleNamespace(
            version="2",
            status="PENDING",
        )

        with self.assertRaisesRegex(RuntimeError, "not READY"):
            self.run_workflow()

        self.mock_validate.assert_not_called()
        self.mock_promote.assert_not_called()

    def test_signature_validation_failure_does_not_promote(self):
        self.mock_validate.side_effect = RuntimeError(
            "Model signature does not match canonical feature schema."
        )

        with self.assertRaisesRegex(RuntimeError, "signature"):
            self.run_workflow()

        self.mock_promote.assert_not_called()

    def test_inference_validation_failure_does_not_promote(self):
        self.mock_validate.side_effect = RuntimeError(
            "Model predictions contain non-finite values."
        )

        with self.assertRaisesRegex(RuntimeError, "non-finite"):
            self.run_workflow()

        self.mock_promote.assert_not_called()

    def test_successful_validation_promotes_and_verifies_champion(self):
        result = self.run_workflow()

        self.assertEqual(result["status"], "PROMOTED")
        self.assertEqual(result["version"], "2")

        self.mock_select.assert_called_once()
        self.assertEqual(
            self.mock_select.call_args.kwargs["evaluation_run_ids"],
            set(self.run_ids),
        )

        self.mock_register.assert_called_once()
        self.mock_validate.assert_called_once()
        self.mock_promote.assert_called_once_with(
            client=self.client,
            version="2",
        )


if __name__ == "__main__":
    unittest.main()
