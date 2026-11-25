
import numpy as np
import pandas as pd

from .config import (
    TARGET_COLUMN,
    TIME_COLUMN,
    PREDICTION_COLUMN,
)


def predict(model, features_df, feature_columns):
    """
    Generate predictions using the MLflow production model.

    The canonical feature configuration defines input names and order.
    Preprocessing is handled inside the registered MLflow model.
    """

    prediction_df = features_df.copy()

    excluded_columns = {
        TIME_COLUMN,
        TARGET_COLUMN,
    }

    available_features = [
        column
        for column in prediction_df.columns
        if column not in excluded_columns
    ]

    missing_columns = [
        column
        for column in feature_columns
        if column not in available_features
    ]

    unexpected_columns = [
        column
        for column in available_features
        if column not in feature_columns
    ]

    if missing_columns or unexpected_columns:
        raise ValueError(
            "Feature schema mismatch. "
            f"Missing={missing_columns}, "
            f"unexpected={unexpected_columns}"
        )

    model_input = prediction_df[feature_columns].copy()

    for column in feature_columns:
        model_input[column] = pd.to_numeric(
            model_input[column],
            errors="raise",
        ).astype("float64")

    if not np.isfinite(model_input.to_numpy()).all():
        raise ValueError(
            "Model input contains non-finite feature values."
        )

    predictions = np.asarray(
        model.predict(model_input),
        dtype=np.float64,
    ).reshape(-1)

    if len(predictions) != len(prediction_df):
        raise RuntimeError(
            "Prediction count does not match input row count."
        )

    if not np.isfinite(predictions).all():
        raise RuntimeError(
            "Model returned non-finite predictions."
        )

    prediction_df[PREDICTION_COLUMN] = predictions

    print("\nPredictions generated successfully.")
    print(f"Rows predicted: {len(predictions)}")

    return prediction_df
