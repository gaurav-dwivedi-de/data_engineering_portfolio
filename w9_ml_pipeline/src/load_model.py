
import mlflow
import mlflow.pyfunc

from mlflow_integration.src.config import FEATURE_COLUMNS

from .config import MLFLOW_TRACKING_URI, MODEL_URI


def load_model():
    """
    Load the global production champion from MLflow.
    """

    if not MLFLOW_TRACKING_URI:
        raise RuntimeError(
            "MLFLOW_TRACKING_URI is not configured."
        )

    if len(FEATURE_COLUMNS) != 27:
        raise RuntimeError(
            f"Expected 27 canonical features, found {len(FEATURE_COLUMNS)}."
        )

    if len(set(FEATURE_COLUMNS)) != len(FEATURE_COLUMNS):
        raise RuntimeError(
            "Canonical feature configuration contains duplicate names."
        )

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    print("\nLoading production champion from MLflow...")
    print(f"Tracking URI: {MLFLOW_TRACKING_URI}")
    print(f"Model URI: {MODEL_URI}")

    model = mlflow.pyfunc.load_model(MODEL_URI)

    print("Production champion loaded successfully.")
    print(f"Expected feature count: {len(FEATURE_COLUMNS)}")

    return model, FEATURE_COLUMNS
