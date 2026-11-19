from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import boto3
import joblib
import mlflow
import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    median_absolute_error,
    explained_variance_score,
    r2_score,
    
)
from mlflow.tracking import MlflowClient

from .registration import (
    MODEL_REGISTRY,
    ComparisonResult,
    compare_metrics,
    load_incumbent_model,
    register_candidate,
)
from .config import (
    DATA_PATH,
    DEPLOYMENT_ENV,
    FEATURE_COLUMNS,
    MLFLOW_EXPERIMENT_NAME,
    MLFLOW_TRACKING_URI,
    RANDOM_STATE,
    TARGET_COLUMN,
    TEST_SIZE,
    TIME_COLUMN,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = PROJECT_ROOT / "mlflow_integration" / "artifacts" / "source"
RESULT_ROOT = PROJECT_ROOT / "mlflow_integration" / "results"

BUCKET = os.getenv("S3_BUCKET_NAME")
REGION = os.getenv("AWS_REGION")

MLFLOW_S3_PREFIX = os.getenv("MLFLOW_S3_PREFIX", "mlflow").strip("/")


if not BUCKET:
    raise RuntimeError("S3_BUCKET_NAME is not configured.")

if not REGION:
    raise RuntimeError("AWS_REGION is not configured.")

MLLIB_S3_PREFIX = f"mllib/{DEPLOYMENT_ENV}/"

SKLEARN_PREFIX = "models/"
SPARK_PREFIX = f"{MLLIB_S3_PREFIX}models/"
SPARK_TEST_PREFIX = f"{MLLIB_S3_PREFIX}data/processed/w7_mllib_test.parquet/"
SPARK_EVALUATION_KEY = (
    f"{MLLIB_S3_PREFIX}data/processed/w7_mllib_evaluation.json"
)
SKLEARN_METADATA_KEY = "models/model_metrics.json"


def download_file(s3, key: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    s3.download_file(BUCKET, key, str(destination))

def download_prefix(s3, prefix: str, destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    count = 0

    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for item in page.get("Contents", []):
            key = item["Key"]

            if key.endswith("/"):
                continue

            relative_key = key[len(prefix):]
            target = destination / relative_key
            target.parent.mkdir(parents=True, exist_ok=True)

            s3.download_file(BUCKET, key, str(target))
            count += 1

    if count == 0:
        raise FileNotFoundError(
            f"No S3 objects found under s3://{BUCKET}/{prefix}"
        )

    return count


def download_artifacts() -> dict[str, Path]:
    if ARTIFACT_ROOT.exists():
        shutil.rmtree(ARTIFACT_ROOT)
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)

    s3 = boto3.client("s3", region_name=REGION)
    sklearn_dir = ARTIFACT_ROOT / "sklearn"
    spark_dir = ARTIFACT_ROOT / "spark_mllib"

    for name in (
        "linear_regression_model.pkl",
        "random_forest_model.pkl",
        "best_model.pkl",
        "scaler.pkl",
        "model_metrics.json",
    ):
        download_file(s3, f"{SKLEARN_PREFIX}{name}", sklearn_dir / name)

    for name in (
        "mllib_linear_regression",
        "mllib_linear_regression_scaler",
        "mllib_random_forest",
    ):
        download_prefix(s3, f"{SPARK_PREFIX}{name}/", spark_dir / name)

    spark_test_dir = ARTIFACT_ROOT / "spark_test"
    download_prefix(s3, SPARK_TEST_PREFIX, spark_test_dir)

    source_dir = ARTIFACT_ROOT / "source_metadata"
    download_file(s3, SKLEARN_METADATA_KEY, source_dir / "sklearn_model_metrics.json")
    download_file(
        s3,
        SPARK_EVALUATION_KEY,
        source_dir / "spark_evaluation.json",
    )

    return {
        "sklearn": sklearn_dir,
        "spark": spark_dir,
        "spark_test": spark_test_dir,
        "metadata": source_dir,
    }


def evaluate_predictions(y_true, y_pred) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=float).reshape(-1)
    y_pred = np.asarray(y_pred, dtype=float).reshape(-1)

    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mse": float(mean_squared_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "median_absolute_error": float(median_absolute_error(y_true, y_pred)),
        "explained_variance": float(explained_variance_score(y_true, y_pred)),
    }


def evaluate_sklearn_models(artifact_dir: Path) -> list[dict]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Feature dataset not found: {DATA_PATH}. "
            "Make the W7 feature Parquet file available locally first."
        )

    df = pd.read_parquet(DATA_PATH).dropna().reset_index(drop=True)

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column {TARGET_COLUMN!r} is missing from {DATA_PATH}")

    excluded = {TARGET_COLUMN, TIME_COLUMN}
    feature_names = [column for column in df.columns if column not in excluded]
    X = df[feature_names]
    y = df[TARGET_COLUMN]

    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )

    scaler = joblib.load(artifact_dir / "scaler.pkl")
    scaler_columns = list(getattr(scaler, "feature_names_in_", []))

    if not scaler_columns:
        numeric_columns = X_train.select_dtypes(include=np.number).columns.tolist()
        if len(numeric_columns) != getattr(scaler, "n_features_in_", len(numeric_columns)):
            raise ValueError(
                "Cannot safely determine the scaler's input columns. "
                "Inspect the original W8 training code before evaluating."
            )
        scaler_columns = numeric_columns

    missing = sorted(set(scaler_columns) - set(X_train.columns))
    if missing:
        raise ValueError(f"Scaler expects missing feature columns: {missing}")

    X_test_scaled = X_test.copy()
    scaled_values = scaler.transform(X_test[scaler_columns])

    X_test_scaled = X_test_scaled.astype("float64")
    X_test_scaled.loc[:, scaler_columns] = scaled_values

    results = []
    for model_name, filename in (
        ("sklearn_linear_regression", "linear_regression_model.pkl"),
        ("sklearn_random_forest", "random_forest_model.pkl"),
    ):
        model = joblib.load(artifact_dir / filename)
        started = time.perf_counter()
        predictions = model.predict(X_test_scaled)
        inference_seconds = time.perf_counter() - started

        results.append({
            "model_name": model_name,
            "framework": "scikit-learn",
            "algorithm": model_name.removeprefix("sklearn_"),
            **evaluate_predictions(y_test, predictions),
            "inference_seconds": inference_seconds,
            "test_rows": int(len(y_test)),
            "feature_count": int(X_test_scaled.shape[1]),
            "dataset": str(DATA_PATH),
            "test_method": (
                f"train_test_split(test_size={TEST_SIZE}, "
                f"random_state={RANDOM_STATE})"
            ),
            "training_timestamp": None,
        })

    return results


def evaluate_sklearn_candidates(candidate_run_id: str) -> dict:
    """Compare scikit-learn candidates against registered champion models."""

    from sklearn.pipeline import Pipeline

    if not candidate_run_id:
        raise ValueError("Candidate run ID is required.")

    project_root = Path(__file__).resolve().parents[2]
    candidate_dir = (
        project_root
        / "w8_weather_prediction_model"
        / "models"
        / "candidates"
        / candidate_run_id
    )

    required_files = [
        candidate_dir / "linear_regression_model.pkl",
        candidate_dir / "random_forest_model.pkl",
        candidate_dir / "scaler.pkl",
    ]

    missing = [path for path in required_files if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing candidate artefacts: {missing}"
        )

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Feature dataset not found: {DATA_PATH}"
        )

    df = pd.read_parquet(DATA_PATH).dropna().reset_index(drop=True)

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column {TARGET_COLUMN!r} is missing.")

    feature_names = [
        column for column in df.columns
        if column not in {TARGET_COLUMN, TIME_COLUMN}
    ]

    X = df[feature_names]
    y = df[TARGET_COLUMN]

    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
    )

    scaler = joblib.load(candidate_dir / "scaler.pkl")
    scaler_columns = list(getattr(scaler, "feature_names_in_", []))

    if not scaler_columns:
        scaler_columns = X_train.select_dtypes(
            include=np.number
        ).columns.tolist()

        if len(scaler_columns) != getattr(
            scaler, "n_features_in_", len(scaler_columns)
        ):
            raise ValueError(
                "Cannot safely determine candidate scaler input columns."
            )

    missing_columns = sorted(
        set(scaler_columns) - set(X_train.columns)
    )
    if missing_columns:
        raise ValueError(
            f"Candidate scaler expects missing columns: {missing_columns}"
        )

    X_test_scaled = X_test.copy().astype("float64")
    X_test_scaled.loc[:, scaler_columns] = scaler.transform(
        X_test[scaler_columns]
    )

    validation_data = pd.concat(
        [
            X_test.reset_index(drop=True),
            y_test.rename(TARGET_COLUMN).reset_index(drop=True),
        ],
        axis=1,
    )

    dataset_hash = hashlib.sha256()
    dataset_hash.update(
        "|".join(validation_data.columns).encode()
    )
    dataset_hash.update(
        pd.util.hash_pandas_object(
            validation_data,
            index=False,
        ).values.tobytes()
    )

    dataset_id = f"sha256:{dataset_hash.hexdigest()}"
    protocol = (
        f"sklearn_train_test_split_test_size_{TEST_SIZE}"
        f"_random_state_{RANDOM_STATE}_v1"
    )

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)

    candidate_models = {
        "sklearn_linear_regression": (
            joblib.load(candidate_dir / "linear_regression_model.pkl")
        ),
        "sklearn_random_forest": (
            joblib.load(candidate_dir / "random_forest_model.pkl")
        ),
    }

    results = {}

    for model_key, candidate_estimator in candidate_models.items():
        incumbent = load_incumbent_model(
            client=client,
            model_key=model_key,
        )

        candidate_predictions = candidate_estimator.predict(
            X_test_scaled
        )
        incumbent_predictions = incumbent.model.predict(X_test)

        candidate_metrics = {
            key: evaluate_predictions(y_test, candidate_predictions)[key]
            for key in ("mae", "rmse", "r2")
        }
        incumbent_metrics = {
            key: evaluate_predictions(y_test, incumbent_predictions)[key]
            for key in ("mae", "rmse", "r2")
        }

        comparison = compare_metrics(
            candidate_metrics,
            incumbent_metrics,
            candidate_dataset_id=dataset_id,
            incumbent_dataset_id=dataset_id,
            candidate_protocol=protocol,
            incumbent_protocol=protocol,
        )

        results[model_key] = {
            "candidate_run_id": candidate_run_id,
            "registered_model_name": incumbent.registered_model_name,
            "incumbent_version": incumbent.version,
            "dataset_id": dataset_id,
            "evaluation_protocol": protocol,
            "test_rows": int(len(y_test)),
            "candidate_metrics": candidate_metrics,
            "incumbent_metrics": incumbent_metrics,
            "comparison": comparison.to_dict(),
        }

    return results


def evaluate_spark_models(artifact_dirs: dict[str, Path]) -> list[dict]:
    from pyspark.ml.evaluation import RegressionEvaluator
    from pyspark.ml.feature import StandardScalerModel
    from pyspark.ml.regression import (
        LinearRegressionModel,
        RandomForestRegressionModel,
    )
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder
        .appName("P2-W8-Existing-Model-Evaluation")
        .master(os.getenv("SPARK_MASTER", "local[*]"))
        .config("spark.driver.memory", os.getenv("SPARK_DRIVER_MEMORY", "4g"))
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    try:
        test_df = spark.read.parquet(str(artifact_dirs["spark_test"]))
        evaluator_rmse = RegressionEvaluator(
            labelCol=TARGET_COLUMN, predictionCol="prediction", metricName="rmse"
        )
        evaluator_mae = RegressionEvaluator(
            labelCol=TARGET_COLUMN, predictionCol="prediction", metricName="mae"
        )
        evaluator_r2 = RegressionEvaluator(
            labelCol=TARGET_COLUMN, predictionCol="prediction", metricName="r2"
        )

        spark_models_dir = artifact_dirs["spark"]
        scaler = StandardScalerModel.load(
            str(spark_models_dir / "mllib_linear_regression_scaler")
        )
        scaled_test = scaler.transform(test_df).drop("features").withColumnRenamed(
            "scaled_features", "features"
        )

        models = [
            (
                "spark_mllib_linear_regression",
                "linear_regression",
                LinearRegressionModel.load(
                    str(spark_models_dir / "mllib_linear_regression")
                ),
                scaled_test,
            ),
            (
                "spark_mllib_random_forest",
                "random_forest",
                RandomForestRegressionModel.load(
                    str(spark_models_dir / "mllib_random_forest")
                ),
                test_df,
            ),
        ]

        results = []
        for name, algorithm, model, evaluation_df in models:
            started = time.perf_counter()
            predictions = model.transform(evaluation_df)
            inference_seconds = time.perf_counter() - started

            results.append({
                "model_name": name,
                "framework": "Spark MLlib",
                "algorithm": algorithm,
                "mae": float(evaluator_mae.evaluate(predictions)),
                "rmse": float(evaluator_rmse.evaluate(predictions)),
                "mse": float(evaluator_rmse.evaluate(predictions) ** 2),
                "r2": float(evaluator_r2.evaluate(predictions)),
                "median_absolute_error": None,
                "explained_variance": None,
                "inference_seconds": inference_seconds,
                "test_rows": int(predictions.count()),
                "feature_count": int(
                    test_df.select("features").first()["features"].size
                ),
                "dataset": str(artifact_dirs["spark_test"]),
                "test_method": "Saved P2-W7 Spark MLlib test Parquet",
                "training_timestamp": None,
            })

        return results
    finally:
        spark.stop()


def evaluate_spark_candidates(candidate_run_id: str) -> dict:
    """Compare Spark candidate models against registered champions."""

    import mlflow
    from pyspark.ml.evaluation import RegressionEvaluator
    from pyspark.ml.feature import StandardScalerModel
    from pyspark.ml.regression import (
        LinearRegressionModel,
        RandomForestRegressionModel,
    )
    from pyspark.sql import SparkSession

    if not candidate_run_id:
        raise ValueError("Candidate run ID is required.")

    project_root = Path(__file__).resolve().parents[2]
    candidate_root = (
        project_root
        / "p2_w7_spark_mllib"
        / "models"
        / "candidates"
        / candidate_run_id
    )
    candidate_test_path = (
        project_root
        / "p2_w7_spark_mllib"
        / "data"
        / "candidates"
        / candidate_run_id
        / "w7_mllib_test.parquet"
    )

    required_paths = [
        candidate_root / "mllib_linear_regression",
        candidate_root / "mllib_linear_regression_scaler",
        candidate_root / "mllib_random_forest",
        candidate_test_path,
    ]

    missing = [path for path in required_paths if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing candidate artefacts: {missing}"
        )

    parquet_files = sorted(candidate_test_path.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(
            f"No Parquet data files found in {candidate_test_path}"
        )

    dataset_hash = hashlib.sha256()
    for parquet_file in parquet_files:
        dataset_hash.update(parquet_file.name.encode())
        with parquet_file.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                dataset_hash.update(chunk)

    dataset_id = f"sha256:{dataset_hash.hexdigest()}"
    protocol = "spark_chronological_split_80_20_v1"

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)

    spark = (
        SparkSession.builder
        .appName("P2-W8-Spark-Candidate-Evaluation")
        .master(os.getenv("SPARK_MASTER", "local[*]"))
        .config(
            "spark.driver.memory",
            os.getenv("SPARK_DRIVER_MEMORY", "4g"),
        )
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    try:
        test_df = spark.read.parquet(str(candidate_test_path))
        test_rows = test_df.count()

        if test_rows == 0:
            raise ValueError("Candidate test dataset is empty.")

        evaluator_results = {}
        for metric in ("mae", "rmse", "r2"):
            evaluator = RegressionEvaluator(
                labelCol=TARGET_COLUMN,
                predictionCol="prediction",
                metricName=metric,
            )
            evaluator_results[metric] = evaluator

        candidate_scaler = StandardScalerModel.load(
            str(candidate_root / "mllib_linear_regression_scaler")
        )
        candidate_lr = LinearRegressionModel.load(
            str(candidate_root / "mllib_linear_regression")
        )
        candidate_rf = RandomForestRegressionModel.load(
            str(candidate_root / "mllib_random_forest")
        )

        candidate_lr_input = (
            candidate_scaler.transform(test_df)
            .drop("features")
            .withColumnRenamed("scaled_features", "features")
        )

        candidate_models = {
            "spark_linear_regression": (
                candidate_lr,
                candidate_lr_input,
            ),
            "spark_random_forest": (
                candidate_rf,
                test_df,
            ),
        }

        results = {}

        for model_key, (candidate_model, candidate_input) in (
            candidate_models.items()
        ):
            incumbent = load_incumbent_model(
                client=client,
                model_key=model_key,
                spark=spark,
            )

            candidate_predictions = candidate_model.transform(
                candidate_input
            )
            incumbent_predictions = incumbent.model.transform(test_df)

            candidate_metrics = {
                metric: float(evaluator.evaluate(candidate_predictions))
                for metric, evaluator in evaluator_results.items()
            }
            incumbent_metrics = {
                metric: float(evaluator.evaluate(incumbent_predictions))
                for metric, evaluator in evaluator_results.items()
            }

            comparison = compare_metrics(
                candidate_metrics,
                incumbent_metrics,
                candidate_dataset_id=dataset_id,
                incumbent_dataset_id=dataset_id,
                candidate_protocol=protocol,
                incumbent_protocol=protocol,
            )

            results[model_key] = {
                "candidate_run_id": candidate_run_id,
                "registered_model_name": incumbent.registered_model_name,
                "incumbent_version": incumbent.version,
                "dataset_id": dataset_id,
                "evaluation_protocol": protocol,
                "test_rows": test_rows,
                "candidate_metrics": candidate_metrics,
                "incumbent_metrics": incumbent_metrics,
                "comparison": comparison.to_dict(),
            }

        return results

    finally:
        spark.stop()

def cleanup_old_evaluation_runs(
    client,
    experiment_id: str,
    keep_run_ids: set[str],
) -> None:
    from mlflow.entities import ViewType

    runs = client.search_runs(
        experiment_ids=[experiment_id],
        run_view_type=ViewType.ALL,
        max_results=10000,
    )

    old_runs = [
        run
        for run in runs
        if run.data.tags.get("phase") == "P2-W8"
        and run.data.tags.get("evaluation_type") == "existing_model_evaluation"
        and run.info.run_id not in keep_run_ids
    ]

    s3 = boto3.client("s3", region_name=REGION)
    paginator = s3.get_paginator("list_objects_v2")

    deleted_objects = 0

    for run in old_runs:
        run_id = run.info.run_id
        object_prefix = (
            f"{MLFLOW_S3_PREFIX}/{experiment_id}/{run_id}/"
        )

        if run.info.lifecycle_stage == "active":
            client.delete_run(run_id)

        for page in paginator.paginate(
            Bucket=BUCKET,
            Prefix=object_prefix,
        ):
            objects = [
                {"Key": item["Key"]}
                for item in page.get("Contents", [])
            ]

            if objects:
                response = s3.delete_objects(
                    Bucket=BUCKET,
                    Delete={"Objects": objects},
                )

                deleted_objects += len(
                    response.get("Deleted", [])
                )

                errors = response.get("Errors", [])
                if errors:
                    raise RuntimeError(
                        f"Failed to delete S3 artifacts for run {run_id}: "
                        f"{errors}"
                    )

    print(
        f"MLflow retention completed: "
        f"kept {len(keep_run_ids)} latest runs, "
        f"processed {len(old_runs)} old runs, "
        f"deleted {deleted_objects} S3 objects."
    )
def log_to_mlflow(results: list[dict], artifact_dirs: dict[str, Path]) -> None:
    import mlflow
    from mlflow.tracking import MlflowClient

    if len(results) != 4:
        raise RuntimeError(
            f"Expected 4 evaluation results, received {len(results)}. "
            "MLflow retention was not executed."
        )

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    experiment = mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    client = MlflowClient()

    new_run_ids = set()

    for result in results:
        run_name = f"P2-W8 evaluation - {result['model_name']}"

        with mlflow.start_run(run_name=run_name):
            mlflow.set_tags({
                "phase": "P2-W8",
                "evaluation_type": "existing_model_evaluation",
                "framework": result["framework"],
                "algorithm": result["algorithm"],
                "test_method": result["test_method"],
                "source": "AWS S3 saved artifacts",
            })

            for key in (
                "mae", "rmse", "mse", "r2", "median_absolute_error",
                "explained_variance", "inference_seconds",
            ):
                value = result.get(key)
                if value is not None and np.isfinite(value):
                    mlflow.log_metric(key, float(value))

            mlflow.log_params({
                "test_rows": result["test_rows"],
                "feature_count": result["feature_count"],
                "dataset": result["dataset"],
                "training_timestamp": result.get("training_timestamp") or "unknown",
                "model_name": result["model_name"],
            })

            mlflow.log_dict(result, "evaluation.json")
            mlflow.log_artifacts(str(artifact_dirs["metadata"]), "source_metadata")

            new_run_ids.add(mlflow.active_run().info.run_id)

    if len(new_run_ids) != 4:
        raise RuntimeError(
            "Four new MLflow runs were not created successfully. "
            "Old runs were preserved."
        )

    print(f"Logged {len(new_run_ids)} P2-W8 evaluation runs.")

    cleanup_old_evaluation_runs(
        client=client,
        experiment_id=experiment.experiment_id,
        keep_run_ids=new_run_ids,
    )


def log_candidate_evaluations(results: dict[str, dict]) -> list[str]:
    """Log candidate-versus-champion evaluation results to MLflow."""

    expected_models = {
        "sklearn_linear_regression",
        "sklearn_random_forest",
        "spark_linear_regression",
        "spark_random_forest",
    }

    if set(results) != expected_models:
        raise RuntimeError(
            "Expected exactly four candidate evaluation results. "
            f"Received: {sorted(results)}"
        )

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    experiment = mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

    run_ids = []
    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)

    for model_key, result in results.items():
        existing_runs = client.search_runs(
            experiment_ids=[experiment.experiment_id],
            filter_string=(
                "tags.evaluation_type = 'candidate_evaluation' "
                f"and tags.candidate_run_id = '{result['candidate_run_id']}' "
                f"and tags.model_key = '{model_key}'"
            ),
            order_by=["start_time DESC"],
            max_results=1,
        )

        if existing_runs:
            existing_run_id = existing_runs[0].info.run_id
            run_ids.append(existing_run_id)
            print(f"Reusing existing evaluation run: {model_key} ({existing_run_id})")
            continue

        with mlflow.start_run(
            experiment_id=experiment.experiment_id,
            run_name=run_name,
        ):
            mlflow.set_tags({
                "phase": "P2-W8",
                "evaluation_type": "candidate_evaluation",
                "model_key": model_key,
                "framework": framework,
                "algorithm": algorithm,
                "registered_model_name": result["registered_model_name"],
                "candidate_run_id": result["candidate_run_id"],
                "incumbent_version": str(result["incumbent_version"]),
                "comparison_accepted": str(accepted).lower(),
                "registration_eligible": str(accepted).lower(),
                "validation_dataset_id": result["dataset_id"],
                "evaluation_protocol": result["evaluation_protocol"],
            })

            mlflow.log_params({
                "model_key": model_key,
                "candidate_run_id": result["candidate_run_id"],
                "registered_model_name": result["registered_model_name"],
                "incumbent_version": str(result["incumbent_version"]),
                "validation_dataset_id": result["dataset_id"],
                "evaluation_protocol": result["evaluation_protocol"],
                "test_rows": result["test_rows"],
            })

            for metric in ("mae", "rmse", "r2"):
                mlflow.log_metric(
                    f"candidate_{metric}",
                    float(candidate_metrics[metric]),
                )
                mlflow.log_metric(
                    f"incumbent_{metric}",
                    float(incumbent_metrics[metric]),
                )

            for metric in (
                "mae_improvement",
                "rmse_change",
                "r2_change",
            ):
                value = comparison.get(metric)
                if value is not None and np.isfinite(value):
                    mlflow.log_metric(metric, float(value))

            mlflow.log_dict(
                result,
                "candidate_evaluation.json",
            )

            run_ids.append(mlflow.active_run().info.run_id)

    if len(run_ids) != 4:
        raise RuntimeError(
            f"Expected four candidate evaluation runs, created {len(run_ids)}."
        )

    print(f"Logged {len(run_ids)} candidate evaluation runs to MLflow.")

    return run_ids


def log_candidate_model_artifacts(
    results: dict[str, dict],
    evaluation_run_ids: list[str],
) -> dict[str, str]:
    """Log accepted candidate models into their evaluation runs."""

    from sklearn.pipeline import Pipeline

    from pyspark.ml.regression import RandomForestRegressionModel
    from pyspark.sql import SparkSession

    if len(results) != 4 or len(evaluation_run_ids) != 4:
        raise ValueError(
            "Expected four candidate results and four evaluation run IDs."
        )

    project_root = Path(__file__).resolve().parents[2]
    model_uris = {}

    for (model_key, result), evaluation_run_id in zip(
        results.items(), evaluation_run_ids
    ):
        if not result["comparison"]["accepted"]:
            print(f"Skipping rejected candidate: {model_key}")
            continue

        candidate_dir = (
            project_root
            / (
                "w8_weather_prediction_model"
                if model_key.startswith("sklearn_")
                else "p2_w7_spark_mllib"
            )
            / "models"
            / "candidates"
            / result["candidate_run_id"]
        )

        with mlflow.start_run(run_id=evaluation_run_id):

            existing_run = mlflow.get_run(evaluation_run_id)
            existing_tags = existing_run.data.tags

            if existing_tags.get("candidate_model_logged") == "true":
                existing_uri = existing_tags.get("candidate_model_uri")

                if not existing_uri:
                    raise RuntimeError(
                        f"Model artifact tag exists but URI is missing: {model_key}"
                    )

                model_uris[model_key] = existing_uri
                print(f"Reusing existing model artifact: {model_key}")
                continue

            if model_key.startswith("sklearn_"):
                scaler = joblib.load(candidate_dir / "scaler.pkl")

                estimator_filename = (
                    "linear_regression_model.pkl"
                    if model_key == "sklearn_linear_regression"
                    else "random_forest_model.pkl"
                )

                estimator = joblib.load(
                    candidate_dir / estimator_filename
                )

                candidate_pipeline = Pipeline([
                    ("scaler", scaler),
                    ("model", estimator),
                ])

                model_log_kwargs = {}

                if model_key == "sklearn_random_forest":
                    model_log_kwargs["skops_trusted_types"] = [
                        "sklearn.tree._tree.Tree"
                    ]

                model_info = mlflow.sklearn.log_model(
                    sk_model=candidate_pipeline,
                    name="candidate_model",
                    **model_log_kwargs,
                )

            elif model_key == "spark_random_forest":
                spark = (
                    SparkSession.builder
                    .appName("P2-W8-Candidate-Model-Logging")
                    .master(os.getenv("SPARK_MASTER", "local[*]"))
                    .config(
                        "spark.driver.memory",
                        os.getenv("SPARK_DRIVER_MEMORY", "4g"),
                    )
                    .getOrCreate()
                )

                spark.sparkContext.setLogLevel("ERROR")

                try:
                    candidate_model = RandomForestRegressionModel.load(
                        str(candidate_dir / "mllib_random_forest")
                    )

                    model_info = mlflow.spark.log_model(
                        spark_model=candidate_model,
                        artifact_path="candidate_model",
                    )
                finally:
                    spark.stop()

            else:
                raise ValueError(
                    f"Unsupported candidate model: {model_key}"
                )

            model_uris[model_key] = model_info.model_uri

            mlflow.set_tags({
                "candidate_model_logged": "true",
                "candidate_model_uri": model_info.model_uri,
            })

            print(
                f"Logged {model_key}: {model_info.model_uri}"
            )

    if len(model_uris) != 3:
        raise RuntimeError(
            f"Expected three accepted model artifacts, "
            f"logged {len(model_uris)}."
        )

    return model_uris


def register_accepted_candidates(
    results: dict[str, dict],
    evaluation_run_ids: list[str],
    model_uris: dict[str, str],
) -> dict[str, dict]:
    """Register accepted candidate models without changing champion aliases."""

    if len(results) != 4 or len(evaluation_run_ids) != 4:
        raise ValueError(
            "Expected four candidate results and four evaluation run IDs."
        )

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)

    run_ids_by_model = dict(zip(results.keys(), evaluation_run_ids))
    registered_versions = {}

    for model_key, result in results.items():
        comparison_data = result["comparison"]

        if not comparison_data["accepted"]:
            print(f"Skipping rejected candidate registration: {model_key}")
            continue

        model_uri = model_uris.get(model_key)

        if not model_uri:
            raise RuntimeError(
                f"Missing logged model URI for accepted candidate: {model_key}"
            )

        comparison = ComparisonResult(**comparison_data)

        version = register_candidate(
            client=client,
            registered_model_name=result["registered_model_name"],
            model_uri=model_uri,
            evaluation_run_id=run_ids_by_model[model_key],
            comparison=comparison,
            validation_dataset_id=result["dataset_id"],
            evaluation_protocol=result["evaluation_protocol"],
        )

        if version is None:
            raise RuntimeError(
                f"Registration unexpectedly skipped accepted candidate: {model_key}"
            )

        if version.status != "READY":
            raise RuntimeError(
                f"Model registration is not READY: "
                f"{model_key}, version={version.version}, "
                f"status={version.status}"
            )

        registered_versions[model_key] = {
            "registered_model_name": result["registered_model_name"],
            "version": version.version,
            "status": version.status,
            "model_uri": model_uri,
        }

        print(
            f"Registered {model_key}: "
            f"{result['registered_model_name']} "
            f"version {version.version} ({version.status})"
        )

    if len(registered_versions) != 3:
        raise RuntimeError(
            f"Expected three registered candidates, "
            f"received {len(registered_versions)}."
        )

    return registered_versions


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate existing sklearn and Spark MLlib models without retraining."
    )

    parser.add_argument(
        "--log-mlflow",
        action="store_true",
        help="Log evaluation results to MLflow after evaluation completes.",
    )

    parser.add_argument(
        "--evaluate-candidates",
        action="store_true",
        help="Evaluate candidate models against registered champions and log comparisons.",
    )

    parser.add_argument(
        "--sklearn-candidate-run-id",
        type=str,
        help="MLflow run ID containing candidate scikit-learn models.",
    )

    parser.add_argument(
        "--spark-candidate-run-id",
        type=str,
        help="MLflow run ID containing candidate Spark MLlib models.",
    )

    args = parser.parse_args()

    if args.evaluate_candidates:
        if not args.sklearn_candidate_run_id:
            parser.error(
                "--sklearn-candidate-run-id is required with --evaluate-candidates."
            )

        if not args.spark_candidate_run_id:
            parser.error(
                "--spark-candidate-run-id is required with --evaluate-candidates."
            )

        print("Evaluating candidate scikit-learn models...")
        candidate_results = evaluate_sklearn_candidates(
            args.sklearn_candidate_run_id
        )

        print("Evaluating candidate Spark MLlib models...")
        candidate_results.update(
            evaluate_spark_candidates(args.spark_candidate_run_id)
        )

        evaluation_run_ids = log_candidate_evaluations(candidate_results)

        candidate_model_uris = log_candidate_model_artifacts(
            candidate_results,
            evaluation_run_ids,
        )

        registered_versions = register_accepted_candidates(
            candidate_results,
            evaluation_run_ids,
            candidate_model_uris,
        )

        print("\nRegistered candidate model versions:")
        for model_key, details in registered_versions.items():
            print(
                f"{model_key}: "
                f"{details['registered_model_name']} "
                f"version {details['version']} "
                f"({details['status']})"
            )

        print("\nLogged candidate model artifacts:")
        for model_key, model_uri in candidate_model_uris.items():
            print(f"{model_key}: {model_uri}")

        print("\nCandidate comparison decisions:")
        for model_key, result in candidate_results.items():
            decision = (
                "ACCEPTED"
                if result["comparison"]["accepted"]
                else "REJECTED"
            )
            print(f"{model_key}: {decision}")

        return

    
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)

    for report_name in (
        "p2_w8_evaluation.csv",
        "p2_w8_evaluation.json",
    ):
        report_path = RESULT_ROOT / report_name
        if report_path.exists():
            report_path.unlink()

    print(f"Downloading existing artifacts from s3://{BUCKET}/ ...")


    artifact_dirs = download_artifacts()

    print("Evaluating saved scikit-learn models ...")
    results = evaluate_sklearn_models(artifact_dirs["sklearn"])

    print("Evaluating saved Spark MLlib models ...")
    results.extend(evaluate_spark_models(artifact_dirs))

    timestamp = datetime.now(timezone.utc).isoformat()
    for result in results:
        result["evaluation_timestamp_utc"] = timestamp
        result["phase"] = "P2-W8"
        result["training_timestamp"] = result.get("training_timestamp") or "unknown"

    csv_path = RESULT_ROOT / "p2_w8_evaluation.csv"
    json_path = RESULT_ROOT / "p2_w8_evaluation.json"

    pd.DataFrame(results).to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("\nEvaluation results:")
    print(pd.DataFrame(results)[
        ["model_name", "mae", "rmse", "r2", "test_rows", "test_method"]
    ].to_string(index=False))
    print(f"\nCSV report:  {csv_path}")
    print(f"JSON report: {json_path}")

    if args.log_mlflow:
        log_to_mlflow(results, artifact_dirs)


if __name__ == "__main__":
    main()

