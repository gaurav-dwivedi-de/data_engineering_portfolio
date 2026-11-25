import logging

import numpy as np
import pandas as pd

from app.config import MODEL_SOURCE, FEATURE_COLUMNS
from app.model_loader import load_model

logging.basicConfig(level=logging.INFO)


def predict(features):
    """
    Generate a next-hour temperature prediction.

    Supports legacy Joblib models and MLflow
    registered models, including models without
    an MLflow input signature.
    """

    model, scaler = load_model()

    df = pd.DataFrame([features])

    if MODEL_SOURCE == "legacy":
        expected_features = list(model.feature_names_in_)
        input_schema = None

    elif MODEL_SOURCE == "mlflow":
        input_schema = model.metadata.get_input_schema()

        if input_schema is None:
            logging.warning(
                "MLflow model has no input signature. "
                "Using the canonical W7 feature schema."
            )
            expected_features = FEATURE_COLUMNS
        else:
            expected_features = [
                column.name
                for column in input_schema.inputs
            ]

            if expected_features != FEATURE_COLUMNS:
                raise ValueError(
                    "MLflow model signature does not match "
                    "the canonical W7 feature schema."
                )

    else:
        raise ValueError(
            f"Unsupported MODEL_SOURCE: {MODEL_SOURCE}"
        )

    missing_features = [
        feature
        for feature in expected_features
        if feature not in df.columns
    ]

    if missing_features:
        raise ValueError(
            "Missing required features: "
            + ", ".join(missing_features)
        )

    extra_features = [
        feature
        for feature in df.columns
        if feature not in expected_features
    ]

    if extra_features:
        logging.warning(
            "Ignoring unexpected features: %s",
            ", ".join(extra_features),
        )

    df = df.reindex(columns=expected_features)

    if MODEL_SOURCE == "legacy":
        df = df.astype("float64")

    elif input_schema is None:
        df = df.astype("float64")

    else:
        dtype_mapping = {
            "float": "float32",
            "double": "float64",
            "integer": "int32",
            "long": "int64",
        }

        for column in input_schema.inputs:
            column_type = str(column.type).split(".")[-1].lower()

            if column_type not in dtype_mapping:
                raise ValueError(
                    f"Unsupported MLflow input type: "
                    f"{column_type} for feature {column.name}"
                )

            df[column.name] = pd.to_numeric(
                df[column.name],
                errors="raise",
            ).astype(dtype_mapping[column_type])

    if df.isnull().values.any():
        raise ValueError(
            "Prediction input contains missing values."
        )

    if not np.isfinite(
        df.to_numpy(dtype="float64")
    ).all():
        raise ValueError(
            "Prediction input contains non-finite values."
        )

    if MODEL_SOURCE == "legacy":
        numerical_columns = df.select_dtypes(
            include=["number"]
        ).columns

        df = df.copy()
        df[numerical_columns] = scaler.transform(
            df[numerical_columns]
        )

    logging.info(
        "Generating prediction using %s model...",
        MODEL_SOURCE,
    )

    prediction = model.predict(df)

    predicted_temperature = float(prediction[0])

    if not np.isfinite(predicted_temperature):
        raise ValueError(
            "Model returned a non-finite prediction."
        )

    logging.info(
        "Prediction completed: %.2f °C",
        predicted_temperature,
    )

    return predicted_temperature
