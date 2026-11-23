
# The code can run locally and in the Airflow pipeline to upload files to S3.
import logging
import os
import re
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


AWS_REGION = os.getenv("AWS_REGION")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


if not AWS_REGION:
    raise RuntimeError("AWS_REGION is not configured.")

if not S3_BUCKET_NAME:
    raise RuntimeError("S3_BUCKET_NAME is not configured.")


s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    config=Config(
        retries={
            "max_attempts": 3,
            "mode": "standard",
        }
    ),
)


# W7 feature dataset

W7_FEATURE_FILE = Path(
    "w7_feature_engineering/data/processed/"
    "w7_features_final.parquet"
)

W7_S3_KEY = "features/w7_features_final.parquet"


# W8 model files

W8_MODEL_FILE = Path(
    "w8_weather_prediction_model/models/"
    "best_model.pkl"
)

W8_SCALER_FILE = Path(
    "w8_weather_prediction_model/models/"
    "scaler.pkl"
)

W8_METRICS_FILE = Path(
    "w8_weather_prediction_model/models/"
    "model_metrics.json"
)

W8_MODEL_S3_KEY = "models/best_model.pkl"
W8_SCALER_S3_KEY = "models/scaler.pkl"
W8_METRICS_S3_KEY = "models/model_metrics.json"


# W9 prediction file

W9_PREDICTION_FILE = Path(
    "w9_ml_pipeline/data/predictions/"
    "weather_predictions.csv"
)

W9_PREDICTION_S3_KEY = "predictions/weather_predictions.csv"


# P2-W7 Spark MLlib artifacts

P2_W7_ROOT = (
    Path(__file__).resolve().parents[1]
    / "p2_w7_spark_mllib"
)

W8_ROOT = Path("/opt/airflow/w8")

DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV")

if DEPLOYMENT_ENV not in {"dev", "prod"}:
    raise RuntimeError(
        "DEPLOYMENT_ENV must be configured as 'dev' or 'prod'."
    )

MLLIB_S3_PREFIX = f"mllib/{DEPLOYMENT_ENV}/"

MLFLOW_S3_PREFIX = os.getenv(
    "MLFLOW_S3_PREFIX",
    "mlflow",
).strip("/")


def upload_file(local_file, s3_key, description):
    """Upload one local file to S3."""

    local_file = Path(local_file)

    if not local_file.is_file():
        raise FileNotFoundError(
            f"{description} not found: {local_file}"
        )

    logger.info(
        "Uploading %s: %s",
        description,
        local_file,
    )

    logger.info(
        "S3 destination: s3://%s/%s",
        S3_BUCKET_NAME,
        s3_key,
    )

    try:
        s3_client.upload_file(
            str(local_file),
            S3_BUCKET_NAME,
            s3_key,
        )

    except ClientError as exc:
        logger.error(
            "%s upload failed: %s",
            description,
            exc,
        )

        raise RuntimeError(
            f"Failed to upload {description}."
        ) from exc

    s3_uri = f"s3://{S3_BUCKET_NAME}/{s3_key}"

    logger.info(
        "%s upload successful: %s",
        description,
        s3_uri,
    )

    return s3_uri


# Original W7-W9 upload functions
# Their paths and S3 keys remain unchanged.


def upload_w7_features():
    """Upload the W7 feature dataset."""

    return upload_file(
        W7_FEATURE_FILE,
        W7_S3_KEY,
        "W7 feature dataset",
    )


def upload_w8_model():
    """Upload the W8 trained model."""

    return upload_file(
        W8_MODEL_FILE,
        W8_MODEL_S3_KEY,
        "W8 best model",
    )


def upload_w8_scaler():
    """Upload the W8 scaler."""

    return upload_file(
        W8_SCALER_FILE,
        W8_SCALER_S3_KEY,
        "W8 scaler",
    )


def upload_w8_metrics():
    """Upload the W8 model metrics."""

    return upload_file(
        W8_METRICS_FILE,
        W8_METRICS_S3_KEY,
        "W8 model metrics",
    )


def upload_w9_predictions():
    """Upload the W9 prediction CSV."""

    return upload_file(
        W9_PREDICTION_FILE,
        W9_PREDICTION_S3_KEY,
        "W9 prediction dataset",
    )


def delete_s3_prefix(s3_prefix):
    """Delete existing S3 objects under a specific prefix."""

    prefix = f"{s3_prefix.strip('/')}/"
    paginator = s3_client.get_paginator("list_objects_v2")
    deleted_count = 0

    for page in paginator.paginate(
        Bucket=S3_BUCKET_NAME,
        Prefix=prefix,
    ):
        objects = [
            {"Key": obj["Key"]}
            for obj in page.get("Contents", [])
        ]

        for start in range(0, len(objects), 1000):
            batch = objects[start:start + 1000]

            if not batch:
                continue

            response = s3_client.delete_objects(
                Bucket=S3_BUCKET_NAME,
                Delete={
                    "Objects": batch,
                    "Quiet": True,
                },
            )

            errors = response.get("Errors", [])

            if errors:
                raise RuntimeError(
                    f"Failed to delete S3 objects under {prefix}: "
                    f"{errors}"
                )

            deleted_count += len(batch)

    logger.info(
        "Deleted %s existing objects under s3://%s/%s",
        deleted_count,
        S3_BUCKET_NAME,
        prefix,
    )


def validate_spark_model_directory(model_dir: Path) -> None:
    """Validate the required data and metadata files of a Spark model."""

    if not model_dir.is_dir():
        raise FileNotFoundError(
            f"Spark baseline model directory not found: {model_dir}"
        )

    for required_subdir in ("data", "metadata"):
        subdir = model_dir / required_subdir

        if not subdir.is_dir():
            raise FileNotFoundError(
                f"Missing Spark model directory: {subdir}"
            )

        valid_files = [
            path
            for path in subdir.rglob("*")
            if (
                path.is_file()
                and path.name != "_SUCCESS"
                and not path.name.endswith(".crc")
                and path.stat().st_size > 0
            )
        ]

        if not valid_files:
            raise RuntimeError(
                f"Incomplete Spark baseline model: {model_dir}. "
                f"No non-empty data files found in {subdir}."
            )

    logger.info(
        "Validated Spark baseline model: %s",
        model_dir.name,
    )


def verify_s3_spark_model_directory(s3_prefix: str) -> None:
    """Verify that a Spark model's data and metadata exist in S3."""

    paginator = s3_client.get_paginator("list_objects_v2")

    for required_subdir in ("data", "metadata"):
        prefix = f"{s3_prefix}/{required_subdir}/"

        valid_objects = []

        for page in paginator.paginate(
            Bucket=S3_BUCKET_NAME,
            Prefix=prefix,
        ):
            for item in page.get("Contents", []):
                key = item["Key"]
                filename = key.rsplit("/", 1)[-1]

                if (
                    filename != "_SUCCESS"
                    and not filename.endswith(".crc")
                    and item["Size"] > 0
                ):
                    valid_objects.append(key)

        if not valid_objects:
            raise RuntimeError(
                f"Incomplete Spark baseline in S3: "
                f"s3://{S3_BUCKET_NAME}/{prefix}"
            )

    logger.info(
        "Verified Spark baseline in S3: s3://%s/%s",
        S3_BUCKET_NAME,
        s3_prefix,
    )

# P2-W7 recursive directory upload

def upload_directory(local_dir, s3_prefix, replace=False):
    """Upload a directory recursively, preserving relative paths."""

    local_dir = Path(local_dir)

    if not local_dir.is_dir():
        raise FileNotFoundError(
            f"P2-W7 directory not found: {local_dir}"
        )

    files = sorted(
        path
        for path in local_dir.rglob("*")
        if path.is_file()
        and not path.name.endswith(".crc")
        and path.name != "_SUCCESS"
    )

    if not files:
        if replace:
            raise FileNotFoundError(
                f"No uploadable files found in directory: {local_dir}"
            )

        logger.info(
            "No files to upload in directory: %s",
            local_dir,
        )
        return

    # Delete old objects only when explicitly requested.
    if replace:
        delete_s3_prefix(s3_prefix)

    for local_file in files:
        relative_path = local_file.relative_to(local_dir)

        s3_key = (
            f"{s3_prefix.rstrip('/')}/"
            f"{relative_path.as_posix()}"
        )

        upload_file(
            local_file,
            s3_key,
            f"P2-W7 artifact: {relative_path.as_posix()}",
        )

    logger.info(
        "Uploaded %s files to s3://%s/%s",
        len(files),
        S3_BUCKET_NAME,
        s3_prefix.rstrip("/"),
    )


def validate_candidate_run_id(candidate_run_id: str) -> str:
    """Validate the candidate UUID before constructing S3 paths."""

    if not re.fullmatch(r"[0-9a-fA-F]{32}", candidate_run_id or ""):
        raise ValueError(
            f"Invalid candidate run ID: {candidate_run_id!r}"
        )

    return candidate_run_id


def upload_sklearn_candidate(candidate_run_id: str):
    """Upload all W8 candidate model artifacts to S3."""

    candidate_run_id = validate_candidate_run_id(
        candidate_run_id
    )

    candidate_dir = (
        W8_ROOT
        / "models"
        / "candidates"
        / candidate_run_id
    )

    required_files = [
        "linear_regression_model.pkl",
        "random_forest_model.pkl",
        "scaler.pkl",
    ]

    missing = [
        candidate_dir / filename
        for filename in required_files
        if not (candidate_dir / filename).is_file()
    ]

    if missing:
        raise FileNotFoundError(
            f"Missing W8 candidate files: {missing}"
        )

    s3_prefix = (
        f"{MLFLOW_S3_PREFIX}/candidates/sklearn/"
        f"{candidate_run_id}"
    )

    upload_directory(
        candidate_dir,
        s3_prefix,
        replace=False,
    )

    logger.info(
        "W8 candidate upload completed: s3://%s/%s/",
        S3_BUCKET_NAME,
        s3_prefix,
    )


def upload_spark_candidate(candidate_run_id: str):
    """Upload Spark candidate models and test dataset to S3."""

    candidate_run_id = validate_candidate_run_id(
        candidate_run_id
    )

    candidate_models_dir = (
        P2_W7_ROOT
        / "models"
        / "candidates"
        / candidate_run_id
    )

    candidate_test_dir = (
        P2_W7_ROOT
        / "data"
        / "candidates"
        / candidate_run_id
        / "w7_mllib_test.parquet"
    )

    required_model_dirs = [
        "mllib_linear_regression",
        "mllib_linear_regression_scaler",
        "mllib_random_forest",
    ]

    missing_models = [
        candidate_models_dir / name
        for name in required_model_dirs
        if not (
            (candidate_models_dir / name).is_dir()
            and any(
                path.is_file()
                for path in (
                    candidate_models_dir / name
                ).rglob("*")
            )
        )
    ]

    if missing_models:
        raise FileNotFoundError(
            f"Missing Spark candidate models: {missing_models}"
        )

    if not candidate_test_dir.is_dir():
        raise FileNotFoundError(
            f"Spark candidate test data not found: {candidate_test_dir}"
        )

    parquet_files = list(
        candidate_test_dir.rglob("*.parquet")
    )

    if not parquet_files:
        raise FileNotFoundError(
            f"No Parquet files found in Spark candidate test dataset: "
            f"{candidate_test_dir}"
        )

    s3_prefix = (
        f"{MLFLOW_S3_PREFIX}/candidates/spark/"
        f"{candidate_run_id}"
    )

    upload_directory(
        candidate_models_dir,
        f"{s3_prefix}/models",
        replace=False,
    )

    upload_directory(
        candidate_test_dir,
        f"{s3_prefix}/data/w7_mllib_test.parquet",
        replace=False,
    )

    logger.info(
        "Spark candidate upload completed: s3://%s/%s/",
        S3_BUCKET_NAME,
        s3_prefix,
    )



def upload_p2_w7_artifacts():
    """Upload P2-W7 processed data, figures and models to S3."""

    directories = {
        "data/processed": P2_W7_ROOT / "data" / "processed",
        "figures": P2_W7_ROOT / "figures",
        "models": P2_W7_ROOT / "models",
    }

    if not P2_W7_ROOT.is_dir():
        raise FileNotFoundError(
            f"P2-W7 project directory not found: {P2_W7_ROOT}"
        )

    
    required_spark_baselines = {
        "mllib_linear_regression",
        "mllib_linear_regression_scaler",
        "mllib_random_forest",
    }

    models_dir = P2_W7_ROOT / "models"

    if not models_dir.is_dir():
        raise FileNotFoundError(
            f"P2-W7 models directory not found: {models_dir}"
        )

    for model_name in sorted(required_spark_baselines):
        validate_spark_model_directory(
            models_dir / model_name
        )


    for relative_path, directory in directories.items():
        if not directory.is_dir():
            if relative_path == "figures":
                logger.info(
                    "Skipping optional P2-W7 figures directory: %s",
                    directory,
                )
                continue

            raise FileNotFoundError(
                f"P2-W7 {relative_path} directory not found: "
                f"{directory}"
            )

        if relative_path == "figures" and not any(
            path.is_file()
            for path in directory.rglob("*")
        ):
            logger.info(
                "Skipping empty P2-W7 figures directory: %s",
                directory,
            )
            continue

        if relative_path != "models":
            upload_directory(
                directory,
                f"{MLLIB_S3_PREFIX.rstrip('/')}/{relative_path}",
                replace=False,
            )
            continue


        for model_dir in sorted(directory.iterdir()):
            if model_dir.name == "candidates":
                logger.info(
                    "Skipping candidate models in production upload: %s",
                    model_dir,
                )
                continue

            if not model_dir.is_dir():
                if model_dir.is_file():
                    upload_file(
                        model_dir,
                        f"{MLLIB_S3_PREFIX.rstrip('/')}/models/"
                        f"{model_dir.name}",
                        f"P2-W7 model artifact: {model_dir.name}",
                    )
                continue

            
            model_s3_prefix = (
                f"{MLLIB_S3_PREFIX.rstrip('/')}/models/"
                f"{model_dir.name}"
            )

            upload_directory(
                model_dir,
                model_s3_prefix,
                replace=False,
            )

            if model_dir.name in required_spark_baselines:
                verify_s3_spark_model_directory(
                    model_s3_prefix
                )


    logger.info(
        "P2-W7 artifacts uploaded to s3://%s/%s",
        S3_BUCKET_NAME,
        MLLIB_S3_PREFIX,
    )


# Airflow upload entry point
# Keep the original Airflow absolute paths unchanged.


def upload_airflow_artifacts():
    """Upload W7-W9 and P2-W7 artifacts from Airflow."""

    # W7 feature dataset
    upload_file(
        "/opt/airflow/w7/data/processed/w7_features_final.parquet",
        "features/w7_features_final.parquet",
        "W7 feature dataset",
    )

    # W8 best model
    upload_file(
        "/opt/airflow/w8/models/best_model.pkl",
        "models/best_model.pkl",
        "W8 best model",
    )

    # W8 scaler
    upload_file(
        "/opt/airflow/w8/models/scaler.pkl",
        "models/scaler.pkl",
        "W8 scaler",
    )

    # W8 model metrics
    upload_file(
        "/opt/airflow/w8/models/model_metrics.json",
        "models/model_metrics.json",
        "W8 model metrics",
    )

    # W9 predictions
    upload_file(
        "/opt/airflow/w9/data/predictions/weather_predictions.csv",
        "predictions/weather_predictions.csv",
        "W9 prediction dataset",
    )

    logger.info(
        "All selected W7-W9 artifacts uploaded successfully."
    )

    # P2-W7 Spark MLlib artifacts
    upload_p2_w7_artifacts()


# Local execution entry point


if __name__ == "__main__":
    upload_w7_features()
    upload_w8_model()
    upload_w8_scaler()
    upload_w8_metrics()
    upload_w9_predictions()
    upload_p2_w7_artifacts()