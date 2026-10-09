
"""Upload W7-W9 artifacts and refresh P2-W7 Spark MLlib artifacts in S3."""

import logging
import os
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
        retries={"max_attempts": 3, "mode": "standard"}
    ),
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
P2_W7_ROOT = PROJECT_ROOT / "p2_w7_spark_mllib"
MLLIB_S3_PREFIX = "mllib/"


def resolve_path(*candidates):
    """Return the first existing local or Airflow path."""
    for candidate in candidates:
        path = PROJECT_ROOT / candidate
        if path.exists():
            return path

    # Return the first candidate so upload_file reports a useful error.
    return PROJECT_ROOT / candidates[0]


def upload_file(local_file, s3_key, description):
    """Upload one file to S3."""
    local_file = Path(local_file)

    if not local_file.is_file():
        raise FileNotFoundError(
            f"{description} not found: {local_file}"
        )

    logger.info(
        "Uploading %s to s3://%s/%s",
        description,
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
        logger.exception("Upload failed: %s", description)
        raise RuntimeError(
            f"Failed to upload {description}."
        ) from exc

    return f"s3://{S3_BUCKET_NAME}/{s3_key}"


def upload_directory(local_dir, s3_prefix):
    """Upload every file beneath a directory, preserving its structure."""
    local_dir = Path(local_dir)

    if not local_dir.is_dir():
        raise FileNotFoundError(
            f"Directory not found: {local_dir}"
        )

    
    files = sorted(
        path
        for path in local_dir.rglob("*")
        if path.is_file()
        and not path.name.endswith(".crc")
    )


    if not files:
        # S3 has no actual directories; this creates a folder marker.
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=f"{s3_prefix.rstrip('/')}/",
            Body=b"",
        )
        logger.info("Created empty S3 prefix: %s/", s3_prefix)
        return

    for local_file in files:
        relative_path = local_file.relative_to(local_dir)
        s3_key = (
            f"{s3_prefix.rstrip('/')}/"
            f"{relative_path.as_posix()}"
        )

        upload_file(
            local_file,
            s3_key,
            f"Artifact: {relative_path.as_posix()}",
        )


def delete_s3_prefix(s3_prefix):
    """Delete all existing S3 objects under one prefix."""
    logger.info(
        "Removing old S3 artifacts under s3://%s/%s",
        S3_BUCKET_NAME,
        s3_prefix,
    )

    paginator = s3_client.get_paginator("list_objects_v2")

    for page in paginator.paginate(
        Bucket=S3_BUCKET_NAME,
        Prefix=s3_prefix,
    ):
        objects = [
            {"Key": item["Key"]}
            for item in page.get("Contents", [])
        ]

        if objects:
            s3_client.delete_objects(
                Bucket=S3_BUCKET_NAME,
                Delete={"Objects": objects, "Quiet": True},
            )

    logger.info("Old S3 prefix cleared: %s", s3_prefix)


def upload_w7_features():
    """Upload the W7 feature dataset."""
    return upload_file(
        resolve_path(
            Path("w7_feature_engineering/data/processed/"
                 "w7_features_final.parquet"),
        ),
        "features/w7_features_final.parquet",
        "W7 feature dataset",
    )


def upload_w8_model():
    """Upload the W8 best model."""
    return upload_file(
        resolve_path(
            Path("w8_weather_prediction_model/models/best_model.pkl"),
            Path("w8/models/best_model.pkl"),
        ),
        "models/best_model.pkl",
        "W8 best model",
    )


def upload_w8_scaler():
    """Upload the W8 scaler."""
    return upload_file(
        resolve_path(
            Path("w8_weather_prediction_model/models/scaler.pkl"),
            Path("w8/models/scaler.pkl"),
        ),
        "models/scaler.pkl",
        "W8 scaler",
    )


def upload_w8_metrics():
    """Upload the W8 model metrics."""
    return upload_file(
        resolve_path(
            Path("w8_weather_prediction_model/models/model_metrics.json"),
            Path("w8/models/model_metrics.json"),
        ),
        "models/model_metrics.json",
        "W8 model metrics",
    )


def upload_w9_predictions():
    """Upload the W9 prediction CSV."""
    return upload_file(
        resolve_path(
            Path("w9_ml_pipeline/data/predictions/"
                 "weather_predictions.csv"),
            Path("w9/data/predictions/weather_predictions.csv"),
        ),
        "predictions/weather_predictions.csv",
        "W9 prediction dataset",
    )


def upload_p2_w7_artifacts():
    """Replace the S3 mllib prefix with the current P2-W7 artifacts."""
    if not P2_W7_ROOT.is_dir():
        raise FileNotFoundError(
            f"P2-W7 project directory not found: {P2_W7_ROOT}"
        )

    # Validate all required directories before deleting existing S3 data.
    directories = {
        "data/processed": P2_W7_ROOT / "data" / "processed",
        "figures": P2_W7_ROOT / "figures",
        "models": P2_W7_ROOT / "models",
    }

    for name, directory in directories.items():
        if not directory.is_dir():
            raise FileNotFoundError(
                f"P2-W7 {name} directory not found: {directory}"
            )

    # Only remove the mllib prefix. W7, W8 and W9 S3 objects are untouched.
    delete_s3_prefix(MLLIB_S3_PREFIX)

    for name, directory in directories.items():
        upload_directory(
            directory,
            f"mllib/{name}",
        )

    logger.info(
        "P2-W7 artifacts refreshed successfully in s3://%s/mllib/",
        S3_BUCKET_NAME,
    )


def upload_airflow_artifacts():
    """Upload the selected W7-W9 files and refresh P2-W7 artifacts."""
    upload_w7_features()

    upload_w8_model()
    upload_w8_scaler()
    upload_w8_metrics()

    # Keep both W8 candidate models for the planned MLflow comparison.
    upload_file(
        resolve_path(
            Path("w8_weather_prediction_model/models/"
                 "linear_regression_model.pkl"),
            Path("w8/models/linear_regression_model.pkl"),
        ),
        "models/linear_regression_model.pkl",
        "W8 Linear Regression model",
    )

    upload_file(
        resolve_path(
            Path("w8_weather_prediction_model/models/"
                 "random_forest_model.pkl"),
            Path("w8/models/random_forest_model.pkl"),
        ),
        "models/random_forest_model.pkl",
        "W8 Random Forest model",
    )

    upload_w9_predictions()
    upload_p2_w7_artifacts()

    logger.info("All selected W7-W9 and P2-W7 uploads completed.")


if __name__ == "__main__":
    upload_airflow_artifacts()
