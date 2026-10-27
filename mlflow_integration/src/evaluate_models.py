from __future__ import annotations

import argparse
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path

import boto3
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    median_absolute_error,
    explained_variance_score,
    r2_score,
    
)

from config import (
    DATA_PATH,
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
BUCKET = os.getenv("WEATHER_S3_BUCKET", "weather-data-lake-mlops")
REGION = os.getenv("AWS_DEFAULT_REGION", "eu-west-2")

SKLEARN_PREFIX = "models/"
SPARK_PREFIX = "mllib/models/"
SPARK_TEST_PREFIX = "mllib/data/processed/w7_mllib_test.parquet/"
SPARK_EVALUATION_KEY = "mllib/data/processed/w7_mllib_evaluation.json"
SKLEARN_METADATA_KEY = "models/model_metrics.json"


def download_file(s3, key: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    s3.download_file(BUCKET, key, str(destination))


def download_prefix(s3, prefix: str, destination: Path) -> int:
    destination.mkdir(parents=True, exist_ok=True)
    count = 0

    for item in s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix).get(
        "Contents", []
    ):
        key = item["Key"]
        if key.endswith("/"):
            continue

        relative_key = key[len(prefix):]
        target = destination / relative_key
        target.parent.mkdir(parents=True, exist_ok=True)
        s3.download_file(BUCKET, key, str(target))
        count += 1

    if count == 0:
        raise FileNotFoundError(f"No S3 objects found under s3://{BUCKET}/{prefix}")

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


def log_to_mlflow(results: list[dict], artifact_dirs: dict[str, Path]) -> None:
    import mlflow
    from mlflow.tracking import MlflowClient

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
    client = MlflowClient()

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

    print(f"Logged {len(results)} P2-W8 evaluation runs to {MLFLOW_TRACKING_URI}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate existing sklearn and Spark MLlib models without retraining."
    )
    parser.add_argument(
        "--log-mlflow",
        action="store_true",
        help="Log evaluation results to MLflow after evaluation completes.",
    )
    args = parser.parse_args()

    
    
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

