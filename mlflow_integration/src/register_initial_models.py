
import logging
import os
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import mlflow.spark
import pandas as pd

from mlflow.models import infer_signature
from mlflow.tracking import MlflowClient
from pyspark.ml import PipelineModel
from pyspark.ml.regression import (
    LinearRegressionModel,
    RandomForestRegressionModel,
)
from pyspark.ml.feature import StandardScalerModel
from pyspark.sql import SparkSession
from sklearn.pipeline import Pipeline

from config import (
    DATA_PATH,
    FEATURE_COLUMNS,
    MLFLOW_EXPERIMENT_NAME,
    MLFLOW_TRACKING_URI,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = PROJECT_ROOT / "mlflow_integration" / "artifacts" / "source"

SKLEARN_ROOT = ARTIFACT_ROOT / "sklearn"
SPARK_ROOT = ARTIFACT_ROOT / "spark_mllib"
SPARK_TEST_ROOT = ARTIFACT_ROOT / "spark_test"

MODEL_NAMES = {
    "sklearn_linear_regression":
        "weather-intelligence-sklearn-linear-regression",
    "sklearn_random_forest":
        "weather-intelligence-sklearn-random-forest",
    "spark_linear_regression":
        "weather-intelligence-spark-linear-regression",
    "spark_random_forest":
        "weather-intelligence-spark-random-forest",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)


def get_evaluation_runs(client, experiment_id):
    runs = client.search_runs(
        experiment_ids=[experiment_id],
        filter_string=(
            "tags.phase = 'P2-W8' "
            "and tags.evaluation_type = 'existing_model_evaluation'"
        ),
        order_by=["attributes.start_time DESC"],
        max_results=100,
    )

    expected_models = {
        "sklearn_linear_regression",
        "sklearn_random_forest",
        "spark_mllib_linear_regression",
        "spark_mllib_random_forest",
    }

    evaluation_runs = {}

    for run in runs:
        model_name = run.data.params.get("model_name")

        if model_name in expected_models and model_name not in evaluation_runs:
            evaluation_runs[model_name] = run

    missing = expected_models - evaluation_runs.keys()

    if missing:
        raise RuntimeError(
            f"Missing evaluation runs for: {sorted(missing)}"
        )

    for model_name, run in evaluation_runs.items():
        if run.info.status != "FINISHED":
            raise RuntimeError(
                f"Evaluation run for {model_name} is not FINISHED."
            )

        for metric in ("mae", "rmse", "r2"):
            if metric not in run.data.metrics:
                raise RuntimeError(
                    f"Missing {metric} metric for {model_name}."
                )

    return evaluation_runs


def get_or_create_registered_model(client, model_name):
    try:
        registered = client.get_registered_model(model_name)
        versions = client.search_model_versions(
            f"name = '{model_name}'"
        )

        if versions:
            version_numbers = sorted(
                int(version.version) for version in versions
            )

            logger.info(
                "%s already has versions %s. Skipping registration.",
                model_name,
                version_numbers,
            )
            return False

        logger.info(
            "%s exists but has no versions. Continuing registration.",
            model_name,
        )

    except Exception as exc:
        if "RESOURCE_DOES_NOT_EXIST" not in str(exc):
            raise

        client.create_registered_model(model_name)

    return True


def log_baseline_metrics(run, evaluation_run):
    for key, value in evaluation_run.data.metrics.items():
        mlflow.log_metric(key, value)

    mlflow.log_params({
        "baseline_evaluation_run_id": evaluation_run.info.run_id,
        "baseline_test_rows": evaluation_run.data.params.get("test_rows", ""),
        "baseline_feature_count": evaluation_run.data.params.get(
            "feature_count", ""
        ),
        "baseline_dataset": evaluation_run.data.params.get("dataset", ""),
    })


def register_sklearn_model(
    client,
    model_key,
    evaluation_key,
    estimator_filename,
    input_example,
    skops_trusted_types=None,
):
    model_name = MODEL_NAMES[model_key]

    if not get_or_create_registered_model(client, model_name):
        return

    estimator = joblib.load(SKLEARN_ROOT / estimator_filename)
    scaler = joblib.load(SKLEARN_ROOT / "scaler.pkl")

    pipeline = Pipeline([
        ("scaler", scaler),
        ("model", estimator),
    ])

    prediction = pipeline.predict(input_example.head(5))
    signature = infer_signature(input_example.head(5), prediction)

    evaluation_run = evaluation_runs[evaluation_key]

    with mlflow.start_run(
        experiment_id=experiment.experiment_id,
        run_name=f"Initial registration - {model_name}",
        tags={
            "phase": "P2-W8",
            "registration_type": "initial_baseline",
            "framework": "scikit-learn",
            "model_name": model_name,
            "baseline_evaluation_run_id": evaluation_run.info.run_id,
        },
    ) as run:
        log_baseline_metrics(run, evaluation_run)

        mlflow.sklearn.log_model(
            sk_model=pipeline,
            artifact_path="model",
            signature=signature,
            input_example=input_example.head(5),
            skops_trusted_types=skops_trusted_types,
        )

        registered = mlflow.register_model(
            model_uri=f"runs:/{run.info.run_id}/model",
            name=model_name,
            await_registration_for=300,
        )

    logger.info(
        "Registered %s version %s",
        model_name,
        registered.version,
    )


def register_spark_model(
    model_key,
    evaluation_key,
    spark_model,
    framework,
):
    model_name = MODEL_NAMES[model_key]

    if not get_or_create_registered_model(client, model_name):
        return

    evaluation_run = evaluation_runs[evaluation_key]

    with mlflow.start_run(
        experiment_id=experiment.experiment_id,
        run_name=f"Initial registration - {model_name}",
        tags={
            "phase": "P2-W8",
            "registration_type": "initial_baseline",
            "framework": framework,
            "model_name": model_name,
            "baseline_evaluation_run_id": evaluation_run.info.run_id,
        },
    ) as run:
        log_baseline_metrics(run, evaluation_run)

        mlflow.spark.log_model(
            spark_model=spark_model,
            artifact_path="model",
            dfs_tmpdir=f"/tmp/mlflow_spark_{model_key}",
        )

        registered = mlflow.register_model(
            model_uri=f"runs:/{run.info.run_id}/model",
            name=model_name,
            await_registration_for=300,
        )

    logger.info(
        "Registered %s version %s",
        model_name,
        registered.version,
    )


def verify_registry(client):
    logger.info("Verifying registered model versions.")

    for model_name in MODEL_NAMES.values():
        versions = client.search_model_versions(
            f"name = '{model_name}'"
        )

        if not versions:
            raise RuntimeError(
                f"No registered version found for {model_name}."
            )

        version_one = next(
            (
                version for version in versions
                if version.version == "1"
            ),
            None,
        )

        if version_one is None:
            raise RuntimeError(
                f"Version 1 missing for {model_name}."
            )

        if version_one.status != "READY":
            raise RuntimeError(
                f"{model_name} version 1 status: {version_one.status}"
            )

        logger.info(
            "%s | Version %s | %s",
            model_name,
            version_one.version,
            version_one.status,
        )


def main():
    global client, experiment, evaluation_runs

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    client = MlflowClient(
        tracking_uri=MLFLOW_TRACKING_URI
    )

    experiment = client.get_experiment_by_name(
        MLFLOW_EXPERIMENT_NAME
    )

    if experiment is None:
        raise RuntimeError(
            f"Experiment not found: {MLFLOW_EXPERIMENT_NAME}"
        )

    required_paths = [
        SKLEARN_ROOT / "linear_regression_model.pkl",
        SKLEARN_ROOT / "random_forest_model.pkl",
        SKLEARN_ROOT / "scaler.pkl",
        SPARK_ROOT / "mllib_linear_regression",
        SPARK_ROOT / "mllib_linear_regression_scaler",
        SPARK_ROOT / "mllib_random_forest",
    ]

    missing = [path for path in required_paths if not path.exists()]

    if missing:
        raise FileNotFoundError(
            f"Missing source artefacts: {missing}"
        )

    evaluation_runs = get_evaluation_runs(
        client,
        experiment.experiment_id,
    )

    logger.info(
        "Using experiment: %s (%s)",
        experiment.name,
        experiment.experiment_id,
    )

    data = pd.read_parquet(DATA_PATH)
    input_example = data[FEATURE_COLUMNS].dropna().head(5)

    if len(input_example) < 5:
        raise RuntimeError(
            "Insufficient feature records for model input example."
        )

    spark = (
        SparkSession.builder
        .master("local[*]")
        .appName("InitialModelRegistration")
        .getOrCreate()
    )

    try:
        register_sklearn_model(
            client,
            "sklearn_linear_regression",
            "sklearn_linear_regression",
            "linear_regression_model.pkl",
            input_example,
        )

        register_sklearn_model(
            client,
            "sklearn_random_forest",
            "sklearn_random_forest",
            "random_forest_model.pkl",
            input_example,
            skops_trusted_types=["sklearn.tree._tree.Tree"],
        )

        spark_lr = LinearRegressionModel.load(
            str(SPARK_ROOT / "mllib_linear_regression")
        )

        spark_scaler = StandardScalerModel.load(
            str(SPARK_ROOT / "mllib_linear_regression_scaler")
        )

        spark_scaler = spark_scaler.copy({})
        spark_scaler.setOutputCol("features_scaled")

        spark_lr = spark_lr.copy({})
        spark_lr.setFeaturesCol("features_scaled")

        spark_lr_pipeline = PipelineModel(
            stages=[spark_scaler, spark_lr]
        )

        spark_rf = RandomForestRegressionModel.load(
            str(SPARK_ROOT / "mllib_random_forest")
        )

        register_spark_model(
            "spark_linear_regression",
            "spark_mllib_linear_regression",
            spark_lr_pipeline,
            "spark_mllib",
        )

        register_spark_model(
            "spark_random_forest",
            "spark_mllib_random_forest",
            spark_rf,
            "spark_mllib",
        )

    finally:
        spark.stop()

    verify_registry(client)

    logger.info("Initial model registration completed.")


if __name__ == "__main__":
    main()
