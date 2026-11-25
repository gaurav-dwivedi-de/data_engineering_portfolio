
import logging

import numpy as np
import pandas as pd

from app.config import MODEL_SOURCE
from app.model_loader import load_model

logging.basicConfig(level=logging.INFO)


def predict(features):
    """
    Generate a next-hour temperature prediction.

    Supports legacy Joblib models and MLflow
    registered models.

    Parameters
    ----------
    features : dict
        Dictionary containing the engineered
        feature values.

    Returns
    -------
    float
        Predicted next-hour temperature.
    """

    model, scaler = load_model()

    df = pd.DataFrame([features])

    # Determine the expected feature order

    if MODEL_SOURCE == "legacy":

        expected_features = list(
            model.feature_names_in_
        )

        input_schema = None

    elif MODEL_SOURCE == "mlflow":

        input_schema = model.metadata.get_input_schema()

        if input_schema is None:
            raise ValueError(
                "MLflow model does not contain an input schema."
            )

        expected_features = [
            column.name
            for column in input_schema.inputs
        ]

    else:

        raise ValueError(
            f"Unsupported MODEL_SOURCE: {MODEL_SOURCE}"
        )

    # Validate missing features

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

    # Identify unexpected features

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

    # Match the expected feature order

    df = df.reindex(
        columns=expected_features
    )

    # Convert input values to the required data types

    if MODEL_SOURCE == "legacy":

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
            ).astype(
                dtype_mapping[column_type]
            )

    # Validate missing values

    if df.isnull().values.any():

        raise ValueError(
            "Prediction input contains missing values."
        )

    # Validate finite numerical values

    if not np.isfinite(
        df.to_numpy(dtype="float64")
    ).all():

        raise ValueError(
            "Prediction input contains non-finite values."
        )

    # Apply external scaling only to legacy models

    if MODEL_SOURCE == "legacy":

        numerical_columns = df.select_dtypes(
            include=["number"]
        ).columns

        df = df.copy()

        df[numerical_columns] = scaler.transform(
            df[numerical_columns]
        )

    # Generate prediction

    logging.info(
        "Generating prediction using %s model...",
        MODEL_SOURCE,
    )

    prediction = model.predict(df)

    predicted_temperature = float(
        prediction[0]
    )

    if not np.isfinite(predicted_temperature):

        raise ValueError(
            "Model returned a non-finite prediction."
        )

    logging.info(
        "Prediction completed: %.2f °C",
        predicted_temperature,
    )

    return predicted_temperature
