
import logging
import os
from pathlib import Path

import boto3
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

S3_BUCKET = os.getenv("S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

SPARK_BASELINE_S3_PREFIX = os.getenv(
    "MLFLOW_BASELINE_SPARK_PREFIX",
    "mllib/dev/models",
).strip("/")

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

def download_s3_prefix(s3, prefix: str, destination: Path) -> int:
    """
    Download non-empty objects from an S3 prefix while preserving
    the directory structure required by Spark MLlib.
    """
    destination.mkdir(parents=True, exist_ok=True)

    paginator = s3.get_paginator("list_objects_v2")
    downloaded = 0

    for page in paginator.paginate(
        Bucket=S3_BUCKET,
        Prefix=f"{prefix.rstrip('/')}/",
    ):
        for item in page.get("Contents", []):
            key = item["Key"]
            size = item["Size"]

            if key.endswith("/") or size == 0:
                continue

            if key.endswith(".crc"):
                continue

            relative_key = key[len(prefix.rstrip("/")) + 1:]
            target = destination / relative_key

            target.parent.mkdir(parents=True, exist_ok=True)

            s3.download_file(
                S3_BUCKET,
                key,
                str(target),
            )

            downloaded += 1

    if downloaded == 0:
        raise FileNotFoundError(
            f"No usable objects found under "
            f"s3://{S3_BUCKET}/{prefix}"
        )

    return downloaded


def download_baseline_artifacts():
    """
    Download the original sklearn and Spark baseline artifacts
    from S3 into the source directories expected by this script.
    """
    if not S3_BUCKET:
        raise RuntimeError("S3_BUCKET_NAME is not configured.")

    if not AWS_REGION:
        raise RuntimeError("AWS_REGION is not configured.")

    s3 = boto3.client(
        "s3",
        region_name=AWS_REGION,
    )

    SKLEARN_ROOT.mkdir(parents=True, exist_ok=True)
    SPARK_ROOT.mkdir(parents=True, exist_ok=True)

    sklearn_files = [
        "linear_regression_model.pkl",
        "random_forest_model.pkl",
        "scaler.pkl",
    ]

    for filename in sklearn_files:
        key = f"models/{filename}"
        destination = SKLEARN_ROOT / filename

        s3.download_file(
            S3_BUCKET,
            key,
            str(destination),
        )

        if not destination.exists() or destination.stat().st_size == 0:
            raise RuntimeError(
                f"Downloaded sklearn artifact is missing or empty: "
                f"{destination}"
            )

        logger.info("Downloaded sklearn artifact: %s", key)

    spark_downloaded = download_s3_prefix(
        s3=s3,
        prefix=SPARK_BASELINE_S3_PREFIX,
        destination=SPARK_ROOT,
    )

    logger.info(
        "Downloaded %s Spark baseline files from s3://%s/%s",
        spark_downloaded,
        S3_BUCKET,
        SPARK_BASELINE_S3_PREFIX,
    )

    spark_model_dirs = [
        SPARK_ROOT / "mllib_linear_regression",
        SPARK_ROOT / "mllib_linear_regression_scaler",
        SPARK_ROOT / "mllib_random_forest",
    ]

    for model_dir in spark_model_dirs:
        data_files = [
            path
            for path in (model_dir / "data").glob("part-*")
            if path.is_file() and path.stat().st_size > 0
        ]

        metadata_files = [
            path
            for path in (model_dir / "metadata").glob("part-*")
            if path.is_file() and path.stat().st_size > 0
        ]

        if not data_files or not metadata_files:
            raise RuntimeError(
                f"Incomplete Spark baseline artifact: {model_dir}. "
                "Expected non-empty data and metadata files."
            )

        logger.info(
            "Validated Spark model directory: %s",
            model_dir.name,
        )

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


def get_initial_baseline_version(client, model_name):
    """
    Return a READY model version whose source run is tagged
    as an initial baseline. Return None if no baseline exists.
    """
    versions = client.search_model_versions(
        f"name = '{model_name}'"
    )

    baseline_versions = []

    for version in versions:
        if version.status != "READY":
            continue

        if not version.run_id:
            continue

        run = client.get_run(version.run_id)

        if run.data.tags.get("registration_type") == "initial_baseline":
            baseline_versions.append(version)

    if not baseline_versions:
        return None

    return max(
        baseline_versions,
        key=lambda version: int(version.version),
    )


def get_or_create_registered_model(client, model_name):
    """
    Ensure that the registered model exists.
    Do not skip registration merely because a candidate version exists.
    """
    try:
        client.get_registered_model(model_name)

        logger.info(
            "Registered model already exists: %s",
            model_name,
        )

    except Exception as exc:
        if "RESOURCE_DOES_NOT_EXIST" not in str(exc):
            raise

        client.create_registered_model(model_name)

        logger.info(
            "Created registered model: %s",
            model_name,
        )

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

    get_or_create_registered_model(client, model_name)

    existing_baseline = get_initial_baseline_version(
        client,
        model_name,
    )

    if existing_baseline is not None:
        logger.info(
            "Initial baseline already exists for %s: version %s. Skipping.",
            model_name,
            existing_baseline.version,
        )
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

    get_or_create_registered_model(client, model_name)

    existing_baseline = get_initial_baseline_version(
        client,
        model_name,
    )

    if existing_baseline is not None:
        logger.info(
            "Initial baseline already exists for %s: version %s. Skipping.",
            model_name,
            existing_baseline.version,
        )
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

def ensure_champion_alias(client, model_name):
    """
    Create the champion alias only when it does not already exist.
    Never replace an existing champion alias.
    """
    registered = client.get_registered_model(model_name)

    existing_alias = registered.aliases.get("champion")

    if existing_alias:
        logger.info(
            "Champion alias already exists for %s: version %s. Preserving it.",
            model_name,
            existing_alias,
        )
        return

    baseline_version = get_initial_baseline_version(
        client,
        model_name,
    )

    if baseline_version is None:
        raise RuntimeError(
            f"No READY initial baseline version found for {model_name}."
        )

    client.set_registered_model_alias(
        name=model_name,
        alias="champion",
        version=str(baseline_version.version),
    )

    logger.info(
        "Assigned champion alias for %s to baseline version %s.",
        model_name,
        baseline_version.version,
    )

def verify_registry(client):
    logger.info("Verifying registered models and champion aliases.")

    for model_name in MODEL_NAMES.values():
        registered = client.get_registered_model(model_name)

        baseline_version = get_initial_baseline_version(
            client,
            model_name,
        )

        if baseline_version is None:
            raise RuntimeError(
                f"No READY initial baseline version found for {model_name}."
            )

        champion_version = registered.aliases.get("champion")

        if not champion_version:
            raise RuntimeError(
                f"Champion alias is missing for {model_name}."
            )

        versions = client.search_model_versions(
            f"name = '{model_name}'"
        )

        champion = next(
            (
                version
                for version in versions
                if str(version.version) == str(champion_version)
            ),
            None,
        )

        if champion is None or champion.status != "READY":
            raise RuntimeError(
                f"Champion alias for {model_name} does not point "
                f"to a READY model version."
            )

        logger.info(
            "%s | Baseline version %s | Champion version %s | READY",
            model_name,
            baseline_version.version,
            champion.version,
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

    logger.info("Downloading baseline artifacts from S3.")

    download_baseline_artifacts()

    logger.info("Baseline artifacts downloaded successfully.")

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

    for model_name in MODEL_NAMES.values():
        ensure_champion_alias(
            client,
            model_name,
        )

    verify_registry(client)

    logger.info("Initial model registration completed.")


if __name__ == "__main__":
    main()
