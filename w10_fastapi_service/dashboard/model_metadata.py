import logging
import os
from datetime import datetime, timezone

from mlflow import MlflowClient

logging.basicConfig(level=logging.INFO)

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://localhost:30500",
)

MLFLOW_MODEL_NAME = os.getenv(
    "MLFLOW_MODEL_NAME",
    "weather-production-model",
)

MLFLOW_MODEL_ALIAS = os.getenv(
    "MLFLOW_MODEL_ALIAS",
    "champion",
)


def load_production_model_metadata():
    """
    Retrieve production model information from MLflow.

    The registered model version tags provide the selected
    evaluation metrics. The source run provides evaluation
    parameters and the evaluation timestamp.
    """

    client = MlflowClient(
        tracking_uri=MLFLOW_TRACKING_URI
    )

    version = client.get_model_version_by_alias(
        MLFLOW_MODEL_NAME,
        MLFLOW_MODEL_ALIAS,
    )

    run = client.get_run(version.run_id)

    tags = version.tags
    params = run.data.params

    model_key = tags.get(
        "selected_model_key",
        "unknown",
    )

    algorithm_names = {
        "sklearn_linear_regression": "Linear Regression",
        "sklearn_random_forest": "Random Forest",
        "spark_linear_regression": "Spark MLlib Linear Regression",
        "spark_random_forest": "Spark MLlib Random Forest",
    }

    end_time = run.info.end_time or run.info.start_time

    if end_time is None:
        evaluated_at = "Unavailable"
    else:
        evaluated_at = datetime.fromtimestamp(
            end_time / 1000,
            tz=timezone.utc,
        ).strftime("%d %b %Y %H:%M UTC")

    required_tags = [
        "selected_r2",
        "selected_rmse",
        "selected_mae",
        "validation_dataset_id",
    ]

    missing_tags = [
        key for key in required_tags
        if key not in tags
    ]

    if missing_tags:
        raise ValueError(
            "Global champion is missing metadata tags: "
            + ", ".join(missing_tags)
        )

    if "test_rows" not in params:
        raise ValueError(
            "Source evaluation run does not contain test_rows."
        )

    metadata = {
        "model_name": MLFLOW_MODEL_NAME,
        "model_version": version.version,
        "algorithm": algorithm_names.get(
            model_key,
            model_key,
        ),
        "r2": float(tags["selected_r2"]),
        "rmse": float(tags["selected_rmse"]),
        "mae": float(tags["selected_mae"]),
        "evaluation_rows": int(params["test_rows"]),
        "evaluated_at": evaluated_at,
        "evaluation_protocol": tags.get(
            "evaluation_protocol",
            "Unavailable",
        ),
        "dataset_id": tags["validation_dataset_id"],
        "run_id": version.run_id,
        "model_alias": MLFLOW_MODEL_ALIAS,
    }

    logging.info(
        "Loaded MLflow production model metadata: %s v%s",
        metadata["model_name"],
        metadata["model_version"],
    )

    return metadata
