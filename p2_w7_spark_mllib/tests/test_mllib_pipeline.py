"""
Validates the P2-W7 Spark MLlib pipeline artifacts after execution, including
the datasets, train/test split, saved models, evaluation results, and predictions.
It acts as the D5 validation gate without retraining models or modifying the
existing W1-W10 production pipeline.
"""

import json

import pytest
from pyspark.ml.linalg import VectorUDT
from pyspark.ml.regression import (
    LinearRegressionModel,
    RandomForestRegressionModel,
)
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.config import (
    EVALUATION_OUTPUT_PATH,
    LINEAR_REGRESSION_MODEL_PATH,
    MLLIB_CLEAN_PATH,
    MLLIB_FEATURES_PATH,
    MLLIB_INPUT_PATH,
    MLLIB_TEST_PATH,
    MLLIB_TRAIN_PATH,
    PREDICTIONS_OUTPUT_PATH,
    RANDOM_FOREST_MODEL_PATH,
)
from src.evaluate import RANDOM_FOREST_PREDICTIONS_OUTPUT_PATH
from src.train_linear_regression import SCALER_MODEL_PATH


@pytest.fixture(scope="session")
def spark():
    spark = (
        SparkSession.builder
        .appName("p2-w7-mllib-tests")
        .master("local[2]")
        .config("spark.driver.memory", "4g")
        .getOrCreate()
    )

    yield spark

    spark.stop()


def test_required_artifacts_exist():
    required_paths = [
        MLLIB_INPUT_PATH,
        MLLIB_CLEAN_PATH,
        MLLIB_FEATURES_PATH,
        MLLIB_TRAIN_PATH,
        MLLIB_TEST_PATH,
        PREDICTIONS_OUTPUT_PATH,
        RANDOM_FOREST_PREDICTIONS_OUTPUT_PATH,
        EVALUATION_OUTPUT_PATH,
        LINEAR_REGRESSION_MODEL_PATH,
        RANDOM_FOREST_MODEL_PATH,
        SCALER_MODEL_PATH,
    ]

    for path in required_paths:
        assert path.exists(), f"Required artifact does not exist: {path}"


def test_mllib_feature_dataset_schema(spark):
    df = spark.read.parquet(str(MLLIB_FEATURES_PATH))

    assert "time" in df.columns
    assert "features" in df.columns
    assert "target_temp_next_hour" in df.columns

    assert isinstance(
        df.schema["features"].dataType,
        VectorUDT,
    )


def test_mllib_feature_dataset_has_valid_values(spark):
    df = spark.read.parquet(str(MLLIB_FEATURES_PATH))

    invalid_rows = df.filter(
        F.col("time").isNull()
        | F.col("features").isNull()
        | F.col("target_temp_next_hour").isNull()
    ).count()

    assert invalid_rows == 0


def test_clean_dataset_is_smaller_than_input(spark):
    input_rows = spark.read.parquet(str(MLLIB_INPUT_PATH)).count()
    clean_rows = spark.read.parquet(str(MLLIB_CLEAN_PATH)).count()

    assert clean_rows < input_rows
    assert clean_rows > 0


def test_train_test_datasets_are_non_empty(spark):
    train_rows = spark.read.parquet(str(MLLIB_TRAIN_PATH)).count()
    test_rows = spark.read.parquet(str(MLLIB_TEST_PATH)).count()

    assert train_rows > 0
    assert test_rows > 0


def test_train_test_periods_do_not_overlap(spark):
    train_df = spark.read.parquet(str(MLLIB_TRAIN_PATH))
    test_df = spark.read.parquet(str(MLLIB_TEST_PATH))

    train_max = train_df.select(F.max("time")).first()[0]
    test_min = test_df.select(F.min("time")).first()[0]

    assert train_max < test_min


def test_train_test_rows_match_feature_dataset(spark):
    feature_rows = spark.read.parquet(str(MLLIB_FEATURES_PATH)).count()
    train_rows = spark.read.parquet(str(MLLIB_TRAIN_PATH)).count()
    test_rows = spark.read.parquet(str(MLLIB_TEST_PATH)).count()

    assert train_rows + test_rows == feature_rows


def test_linear_regression_model_loads(spark):
    model = LinearRegressionModel.load(
        str(LINEAR_REGRESSION_MODEL_PATH)
    )

    assert model is not None


def test_random_forest_model_loads(spark):
    model = RandomForestRegressionModel.load(
        str(RANDOM_FOREST_MODEL_PATH)
    )

    assert model is not None
    assert model.getNumTrees > 0


def test_evaluation_contains_both_models():
    with open(EVALUATION_OUTPUT_PATH, "r", encoding="utf-8") as file:
        evaluation = json.load(file)

    assert evaluation["framework"] == "Spark MLlib"
    assert "models" in evaluation

    models = evaluation["models"]

    assert "linear_regression" in models
    assert "random_forest" in models

    for model_name in ["linear_regression", "random_forest"]:
        metrics = models[model_name]

        assert "rmse" in metrics
        assert "mae" in metrics
        assert "r2" in metrics


def test_prediction_row_counts_match_test_dataset(spark):
    test_rows = spark.read.parquet(str(MLLIB_TEST_PATH)).count()

    lr_prediction_rows = spark.read.parquet(
        str(PREDICTIONS_OUTPUT_PATH)
    ).count()

    rf_prediction_rows = spark.read.parquet(
        str(RANDOM_FOREST_PREDICTIONS_OUTPUT_PATH)
    ).count()

    assert lr_prediction_rows == test_rows
    assert rf_prediction_rows == test_rows