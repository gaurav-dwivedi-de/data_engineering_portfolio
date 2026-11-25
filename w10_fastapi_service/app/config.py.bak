
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_project_dir(container_name: str, local_name: str) -> Path:
    container_path = PROJECT_ROOT / container_name

    if container_path.is_dir():
        return container_path

    return PROJECT_ROOT / local_name


W7_PROJECT_DIR = resolve_project_dir(
    "w7",
    "w7_feature_engineering",
)

W8_PROJECT_DIR = resolve_project_dir(
    "w8",
    "w8_weather_prediction_model",
)

W9_PROJECT_DIR = resolve_project_dir(
    "w9",
    "w9_ml_pipeline",
)


MODEL_SOURCE = os.getenv(
    "MODEL_SOURCE",
    "legacy",
).strip().lower()

if MODEL_SOURCE not in {"legacy", "mlflow"}:
    raise ValueError(
        "MODEL_SOURCE must be either 'legacy' or 'mlflow'."
    )


MODEL_PATH = Path(
    os.getenv(
        "MODEL_PATH",
        W8_PROJECT_DIR / "models" / "best_model.pkl",
    )
)

MODEL_METRICS_PATH = Path(
    os.getenv(
        "MODEL_METRICS_PATH",
        W8_PROJECT_DIR / "models" / "model_metrics.json",
    )
)

SCALER_PATH = Path(
    os.getenv(
        "SCALER_PATH",
        W8_PROJECT_DIR / "models" / "scaler.pkl",
    )
)


MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://localhost:30500",
)

MLFLOW_MODEL_NAME = os.getenv(
    "MLFLOW_MODEL_NAME",
    "",
).strip()

MLFLOW_MODEL_ALIAS = os.getenv(
    "MLFLOW_MODEL_ALIAS",
    "champion",
).strip()


FEATURE_FILE = Path(
    os.getenv(
        "FEATURE_FILE",
        W7_PROJECT_DIR
        / "data"
        / "processed"
        / "w7_features_final.parquet",
    )
)

PREDICTION_FILE = Path(
    os.getenv(
        "PREDICTION_FILE",
        W9_PROJECT_DIR
        / "data"
        / "predictions"
        / "weather_predictions.csv",
    )
)


logging.info("Model source: %s", MODEL_SOURCE)

if MODEL_SOURCE == "legacy":
    logging.info("Model path: %s", MODEL_PATH)
    logging.info("Scaler path: %s", SCALER_PATH)
else:
    logging.info("MLflow tracking URI: %s", MLFLOW_TRACKING_URI)
    logging.info("MLflow model: %s", MLFLOW_MODEL_NAME)
    logging.info("MLflow alias: %s", MLFLOW_MODEL_ALIAS)

logging.info("Model metrics path: %s", MODEL_METRICS_PATH)
logging.info("Feature file: %s", FEATURE_FILE)
logging.info("Prediction file: %s", PREDICTION_FILE)
