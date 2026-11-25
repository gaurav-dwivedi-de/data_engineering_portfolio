import json
import logging
import os
import tempfile
from pathlib import Path

import mlflow
import mlflow.pyfunc
import mlflow.spark
import numpy as np
import pandas as pd

from mlflow.exceptions import MlflowException
from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient
from pyspark.ml import PipelineModel
from pyspark.ml.linalg import Vectors, VectorUDT
from pyspark.sql import SparkSession
from pyspark.sql.types import StructField, StructType

from .config import (
    DEPLOYMENT_ENV,
    FEATURE_COLUMNS,
    MLFLOW_EXPERIMENT_NAME,
    MLFLOW_TRACKING_URI,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVALUATION_REPORT = (
    PROJECT_ROOT
    / "mlflow_integration"
    / "results"
    / "p2_w8_evaluation.json"
)

PRODUCTION_MODEL_NAME = "weather-intelligence-production"
PRODUCTION_ALIAS = "champion"

CANDIDATE_MODELS = {
    "sklearn_linear_regression":
        "weather-intelligence-sklearn-linear-regression",
    "sklearn_random_forest":
        "weather-intelligence-sklearn-random-forest",
    "spark_mllib_linear_regression":
        "weather-intelligence-spark-linear-regression",
    "spark_mllib_random_forest":
        "weather-intelligence-spark-random-forest",
}

METRIC_KEYS = ("mae", "rmse", "r2")
METRIC_TOLERANCE = 1e-8

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class SparkWeatherPyFunc(mlflow.pyfunc.PythonModel):
    """PyFunc wrapper for the Spark MLlib scaler + Linear Regression pipeline."""

    def __init__(self, feature_columns):
        self.feature_columns = list(feature_columns)
        self.spark = None
        self.pipeline = None

    def load_context(self, context):
        self.spark = (
            SparkSession.builder
            .appName("WeatherProductionPyFunc")
            .getOrCreate()
        )
        self.spark.sparkContext.setLogLevel("ERROR")

        self.pipeline = PipelineModel.load(
            context.artifacts["spark_pipeline"]
        )

    def predict(self, context, model_input, params=None):
        if not isinstance(model_input, pd.DataFrame):
            model_input = pd.DataFrame(model_input)

        missing = [
            column
            for column in self.feature_columns
            if column not in model_input.columns
        ]
        if missing:
            raise ValueError(
                f"Missing required model features: {missing}"
            )

        features = model_input[self.feature_columns].copy()

        try:
            features = features.astype("float64")
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "All model features must be numeric."
            ) from exc

        values = features.to_numpy(dtype="float64")

        if not np.isfinite(values).all():
            raise ValueError(
                "Model input contains null, NaN, or infinite values."
            )

        spark_rows = [
            (Vectors.dense(row.tolist()),)
            for row in values
        ]

        spark_schema = StructType([
            StructField("features", VectorUDT(), nullable=False)
        ])

        spark_features = self.spark.createDataFrame(
            spark_rows,
            schema=spark_schema,
        )

        predictions = (
            self.pipeline
            .transform(spark_features)
            .select("prediction")
            .toPandas()
        )

        return predictions.rename(
            columns={"prediction": "predicted_temperature"}
        )


def load_evaluation_report():
    if not EVALUATION_REPORT.exists():
        raise FileNotFoundError(
            f"Evaluation report not found: {EVALUATION_REPORT}"
        )

    with EVALUATION_REPORT.open("r", encoding="utf-8") as file:
        report = json.load(file)

    if not isinstance(report, list) or not report:
        raise ValueError(
            "Evaluation JSON must contain a non-empty list of model records."
        )

    required = {
        "model_name",
        "mae",
        "rmse",
        "r2",
        "test_rows",
        "test_method",
        "dataset",
    }

    for record in report:
        missing = required.difference(record)
        if missing:
            raise ValueError(
                f"Evaluation record {record.get('model_name')} "
                f"is missing fields: {sorted(missing)}"
            )

        for metric in METRIC_KEYS:
            value = record[metric]
            if value is None or not np.isfinite(float(value)):
                raise ValueError(
                    f"Invalid {metric} for {record['model_name']}: {value}"
                )

    return report


def validate_evaluation_protocol(report):
    """Prevent a global ranking from mixing incompatible holdout protocols."""
    expected_names = set(CANDIDATE_MODELS)
    actual_names = {record["model_name"] for record in report}

    if actual_names != expected_names:
        raise ValueError(
            "Evaluation report must contain exactly these four candidates. "
            f"Expected={sorted(expected_names)}, actual={sorted(actual_names)}"
        )

    test_rows = {int(record["test_rows"]) for record in report}
    test_methods = {record["test_method"] for record in report}
    datasets = {record["dataset"] for record in report}

    if len(test_rows) != 1 or len(test_methods) != 1 or len(datasets) != 1:
        details = [
            {
                "model_name": row["model_name"],
                "test_rows": row["test_rows"],
                "test_method": row["test_method"],
                "dataset": row["dataset"],
            }
            for row in report
        ]
        raise ValueError(
            "The evaluation report does not prove that all four candidates "
            "were evaluated on the same holdout dataset and protocol. "
            "No global production model will be registered. "
            f"Per-model evaluation metadata: {details}"
        )


def select_best_candidate(report):
    """Rank by MAE ascending, RMSE ascending, then R2 descending."""
    return sorted(
        report,
        key=lambda row: (
            float(row["mae"]),
            float(row["rmse"]),
            -float(row["r2"]),
        ),
    )[0]


def get_candidate_version(client, candidate_name):
    try:
        version = client.get_model_version_by_alias(
            candidate_name,
            "champion",
        )
    except MlflowException as exc:
        raise RuntimeError(
            f"Could not resolve champion alias for {candidate_name}. "
            "Register and verify the candidate baseline models first."
        ) from exc

    if version.status != "READY":
        raise RuntimeError(
            f"Candidate {candidate_name} version {version.version} "
            f"is not READY: {version.status}"
        )

    return version


def verify_candidate_metrics(client, version, report_record):
    evaluation_run_id = version.tags.get("baseline_evaluation_run_id")

    if not evaluation_run_id:
        raise RuntimeError(
            f"Candidate version {version.version} has no "
            "baseline_evaluation_run_id tag."
        )

    evaluation_run = client.get_run(evaluation_run_id)

    for metric in METRIC_KEYS:
        expected = float(report_record[metric])
        actual = evaluation_run.data.metrics.get(metric)

        if actual is None or not np.isclose(
            float(actual),
            expected,
            rtol=0,
            atol=METRIC_TOLERANCE,
        ):
            raise RuntimeError(
                f"Candidate metric mismatch for {metric}: "
                f"report={expected}, MLflow evaluation run={actual}. "
                "Refusing to register an unverified candidate."
            )

    return evaluation_run


def get_existing_production_version(
    client,
    source_model_name,
    source_model_version,
):
    try:
        registered_model = client.get_registered_model(
            PRODUCTION_MODEL_NAME
        )
    except MlflowException as exc:
        if "RESOURCE_DOES_NOT_EXIST" in str(exc):
            return None
        raise

    for version in registered_model.latest_versions:
        if (
            version.status == "READY"
            and version.tags.get("source_candidate_model_name")
            == source_model_name
            and version.tags.get("source_candidate_version")
            == str(source_model_version)
        ):
            return version

    return None


def register_production_model(
    client,
    spark,
    selected_record,
    candidate_version,
    evaluation_run,
):
    source_model_name = CANDIDATE_MODELS[
        selected_record["model_name"]
    ]
    source_model_version = str(candidate_version.version)

    existing = get_existing_production_version(
        client,
        source_model_name,
        source_model_version,
    )

    if existing is not None:
        logger.info(
            "Production model already contains this candidate: "
            "%s version %s",
            PRODUCTION_MODEL_NAME,
            existing.version,
        )
        client.set_registered_model_alias(
            PRODUCTION_MODEL_NAME,
            PRODUCTION_ALIAS,
            existing.version,
        )
        return existing

    source_uri = (
        f"models:/{source_model_name}/{source_model_version}"
    )

    logger.info("Loading selected Spark candidate: %s", source_uri)

    source_pipeline = mlflow.spark.load_model(source_uri)

    if not isinstance(source_pipeline, PipelineModel):
        raise TypeError(
            "Selected Spark Linear Regression candidate is not a "
            "PipelineModel. Expected scaler + estimator pipeline."
        )

    with tempfile.TemporaryDirectory(
        prefix="weather_production_model_"
    ) as temporary_directory:
        pipeline_path = Path(temporary_directory) / "spark_pipeline"

        source_pipeline.write().overwrite().save(str(pipeline_path))

        input_example = pd.DataFrame(
            np.zeros((3, len(FEATURE_COLUMNS)), dtype="float64"),
            columns=FEATURE_COLUMNS,
        )
        output_example = pd.DataFrame({
            "predicted_temperature": pd.Series(dtype="float64")
        })

        signature = infer_signature(
            input_example,
            output_example,
        )

        experiment = mlflow.get_experiment_by_name(
            MLFLOW_EXPERIMENT_NAME
        )
        if experiment is None:
            raise RuntimeError(
                f"MLflow experiment not found: {MLFLOW_EXPERIMENT_NAME}"
            )

        with mlflow.start_run(
            experiment_id=experiment.experiment_id,
            run_name="Register global production model",
            tags={
                "phase": "P2-W8",
                "registration_type": "global_production",
                "deployment_env": DEPLOYMENT_ENV,
                "source_candidate_model_name": source_model_name,
                "source_candidate_version": source_model_version,
                "source_candidate_run_id": candidate_version.run_id,
                "evaluation_run_id": evaluation_run.info.run_id,
                "evaluation_report": str(EVALUATION_REPORT),
                "selected_model_key": selected_record["model_name"],
            },
        ) as run:
            for metric in METRIC_KEYS:
                mlflow.log_metric(
                    metric,
                    float(selected_record[metric]),
                )

            mlflow.log_params({
                "source_candidate_model_name": source_model_name,
                "source_candidate_version": source_model_version,
                "source_candidate_run_id": candidate_version.run_id,
                "evaluation_run_id": evaluation_run.info.run_id,
                "test_rows": int(selected_record["test_rows"]),
                "feature_count": len(FEATURE_COLUMNS),
                "test_method": selected_record["test_method"],
                "dataset": selected_record["dataset"],
            })

            mlflow.pyfunc.log_model(
                artifact_path="model",
                python_model=SparkWeatherPyFunc(FEATURE_COLUMNS),
                artifacts={
                    "spark_pipeline": str(pipeline_path)
                },
                signature=signature,
                input_example=input_example,
            )

            model_uri = f"runs:/{run.info.run_id}/model"

        registered = mlflow.register_model(
            model_uri=model_uri,
            name=PRODUCTION_MODEL_NAME,
            await_registration_for=300,
        )

    client.set_model_version_tag(
        PRODUCTION_MODEL_NAME,
        registered.version,
        "source_candidate_model_name",
        source_model_name,
    )
    client.set_model_version_tag(
        PRODUCTION_MODEL_NAME,
        registered.version,
        "source_candidate_version",
        source_model_version,
    )
    client.set_model_version_tag(
        PRODUCTION_MODEL_NAME,
        registered.version,
        "source_candidate_run_id",
        candidate_version.run_id,
    )
    client.set_model_version_tag(
        PRODUCTION_MODEL_NAME,
        registered.version,
        "evaluation_run_id",
        evaluation_run.info.run_id,
    )
    client.set_model_version_tag(
        PRODUCTION_MODEL_NAME,
        registered.version,
        "deployment_env",
        DEPLOYMENT_ENV,
    )

    registered = client.get_model_version(
        PRODUCTION_MODEL_NAME,
        registered.version,
    )

    if registered.status != "READY":
        raise RuntimeError(
            f"Production model version {registered.version} "
            f"is not READY: {registered.status}"
        )

    client.set_registered_model_alias(
        PRODUCTION_MODEL_NAME,
        PRODUCTION_ALIAS,
        registered.version,
    )

    return registered


def verify_production_alias(client, expected_version):
    active = client.get_model_version_by_alias(
        PRODUCTION_MODEL_NAME,
        PRODUCTION_ALIAS,
    )

    if str(active.version) != str(expected_version):
        raise RuntimeError(
            "Production alias verification failed: "
            f"expected version {expected_version}, got {active.version}"
        )

    loaded_model = mlflow.pyfunc.load_model(
        f"models:/{PRODUCTION_MODEL_NAME}@{PRODUCTION_ALIAS}"
    )

    smoke_input = pd.DataFrame(
        np.zeros((1, len(FEATURE_COLUMNS)), dtype="float64"),
        columns=FEATURE_COLUMNS,
    )
    prediction = loaded_model.predict(smoke_input)

    if (
        not isinstance(prediction, pd.DataFrame)
        or "predicted_temperature" not in prediction.columns
        or len(prediction) != 1
        or not np.isfinite(
            float(prediction.iloc[0]["predicted_temperature"])
        )
    ):
        raise RuntimeError(
            "Production model smoke test failed. "
            f"Unexpected prediction output: {prediction}"
        )

    logger.info(
        "Production alias verified: %s@%s",
        PRODUCTION_MODEL_NAME,
        PRODUCTION_ALIAS,
    )
    logger.info(
        "Smoke-test prediction: %.6f",
        float(prediction.iloc[0]["predicted_temperature"]),
    )


def main():
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    client = MlflowClient(
        tracking_uri=MLFLOW_TRACKING_URI
    )

    report = load_evaluation_report()
    validate_evaluation_protocol(report)

    selected_record = select_best_candidate(report)
    source_model_name = CANDIDATE_MODELS[
        selected_record["model_name"]
    ]

    logger.info(
        "Selected candidate: %s (%s)",
        selected_record["model_name"],
        source_model_name,
    )
    logger.info(
        "Metrics: MAE=%.6f RMSE=%.6f R2=%.6f",
        float(selected_record["mae"]),
        float(selected_record["rmse"]),
        float(selected_record["r2"]),
    )

    candidate_version = get_candidate_version(
        client,
        source_model_name,
    )
    evaluation_run = verify_candidate_metrics(
        client,
        candidate_version,
        selected_record,
    )

    spark = (
        SparkSession.builder
        .appName("RegisterWeatherProductionModel")
        .getOrCreate()
    )

    try:
        production_version = register_production_model(
            client,
            spark,
            selected_record,
            candidate_version,
            evaluation_run,
        )
    finally:
        spark.stop()

    verify_production_alias(
        client,
        production_version.version,
    )

    logger.info(
        "Production registration completed: "
        "%s version %s, alias=%s",
        PRODUCTION_MODEL_NAME,
        production_version.version,
        PRODUCTION_ALIAS,
    )


if __name__ == "__main__":
    main()
