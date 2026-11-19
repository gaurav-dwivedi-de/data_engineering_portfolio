
import logging

import joblib
import mlflow
import mlflow.pyfunc

from app.config import (
    MODEL_SOURCE,
    MODEL_PATH,
    SCALER_PATH,
    MLFLOW_TRACKING_URI,
    MLFLOW_MODEL_NAME,
    MLFLOW_MODEL_ALIAS,
)

logging.basicConfig(level=logging.INFO)

_model = None
_scaler = None


def load_model():
    """
    Load and cache the configured prediction model.

    Returns
    -------
    tuple
        (model, scaler)

        Legacy mode:
            (joblib model, fitted scaler)

        MLflow mode:
            (MLflow pyfunc model, None)
    """

    global _model
    global _scaler

    if _model is not None:
        return _model, _scaler

    if MODEL_SOURCE == "legacy":

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file not found:\n{MODEL_PATH}"
            )

        if not SCALER_PATH.exists():
            raise FileNotFoundError(
                f"Scaler file not found:\n{SCALER_PATH}"
            )

        logging.info("Loading legacy model...")

        _model = joblib.load(MODEL_PATH)
        _scaler = joblib.load(SCALER_PATH)

        logging.info(
            "Loaded legacy model %s and scaler %s",
            _model.__class__.__name__,
            _scaler.__class__.__name__,
        )

        return _model, _scaler

    if MODEL_SOURCE == "mlflow":

        if not MLFLOW_MODEL_NAME:
            raise ValueError(
                "MLFLOW_MODEL_NAME must be configured "
                "when MODEL_SOURCE='mlflow'."
            )

        model_uri = (
            f"models:/{MLFLOW_MODEL_NAME}"
            f"@{MLFLOW_MODEL_ALIAS}"
        )

        logging.info(
            "Loading MLflow model from %s",
            model_uri,
        )

        mlflow.set_tracking_uri(
            MLFLOW_TRACKING_URI
        )

        _model = mlflow.pyfunc.load_model(
            model_uri
        )

        _scaler = None

        logging.info(
            "Loaded MLflow model: %s",
            model_uri,
        )

        return _model, _scaler

    raise ValueError(
        f"Unsupported MODEL_SOURCE: {MODEL_SOURCE}"
    )
