import json

from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import StandardScalerModel
from pyspark.ml.regression import LinearRegressionModel
from pyspark.ml.regression import RandomForestRegressionModel
from pyspark.sql import SparkSession

from src.config import (
    EVALUATION_OUTPUT_PATH,
    LINEAR_REGRESSION_MODEL_PATH,
    MLLIB_TEST_PATH,
    PREDICTIONS_OUTPUT_PATH,
    RANDOM_FOREST_MODEL_PATH,
    SPARK_APP_NAME,
    SPARK_DRIVER_MEMORY,
    SPARK_MASTER,
    TARGET_COLUMN,
    TIME_COLUMN,
)


SCALER_MODEL_PATH = (
    LINEAR_REGRESSION_MODEL_PATH.parent
    / "mllib_linear_regression_scaler"
)

RANDOM_FOREST_PREDICTIONS_OUTPUT_PATH = (
    PREDICTIONS_OUTPUT_PATH.parent
    / "w7_mllib_random_forest_predictions.parquet"
)


def create_spark_session():
    return (
        SparkSession.builder
        .appName(SPARK_APP_NAME)
        .master(SPARK_MASTER)
        .config("spark.driver.memory", SPARK_DRIVER_MEMORY)
        .getOrCreate()
    )


def calculate_metrics(predictions):
    rmse_evaluator = RegressionEvaluator(
        labelCol=TARGET_COLUMN,
        predictionCol="prediction",
        metricName="rmse",
    )

    mae_evaluator = RegressionEvaluator(
        labelCol=TARGET_COLUMN,
        predictionCol="prediction",
        metricName="mae",
    )

    r2_evaluator = RegressionEvaluator(
        labelCol=TARGET_COLUMN,
        predictionCol="prediction",
        metricName="r2",
    )

    return {
        "rmse": float(rmse_evaluator.evaluate(predictions)),
        "mae": float(mae_evaluator.evaluate(predictions)),
        "r2": float(r2_evaluator.evaluate(predictions)),
    }


def validate_test_dataset(test_df):
    required_columns = [
        TIME_COLUMN,
        "features",
        TARGET_COLUMN,
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in test_df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )


def evaluate_linear_regression(test_df):
    print("Evaluating Spark MLlib Linear Regression...")

    print(
        f"Loading StandardScaler model: "
        f"{SCALER_MODEL_PATH}"
    )

    scaler_model = StandardScalerModel.load(
        str(SCALER_MODEL_PATH)
    )

    scaled_test_df = scaler_model.transform(test_df)

    scaled_test_df = (
        scaled_test_df
        .select(
            TIME_COLUMN,
            "scaled_features",
            TARGET_COLUMN,
        )
        .withColumnRenamed(
            "scaled_features",
            "features",
        )
    )

    print(
        "Test features transformed using the saved "
        "training StandardScaler."
    )

    print(
        f"Loading Linear Regression model: "
        f"{LINEAR_REGRESSION_MODEL_PATH}"
    )

    model = LinearRegressionModel.load(
        str(LINEAR_REGRESSION_MODEL_PATH)
    )

    predictions = model.transform(scaled_test_df)

    metrics = calculate_metrics(predictions)

    print(f"Linear Regression RMSE: {metrics['rmse']:.6f}")
    print(f"Linear Regression MAE: {metrics['mae']:.6f}")
    print(f"Linear Regression R²: {metrics['r2']:.6f}")

    predictions_output = predictions.select(
        TIME_COLUMN,
        TARGET_COLUMN,
        "prediction",
    )

    predictions_output.write.mode("overwrite").parquet(
        str(PREDICTIONS_OUTPUT_PATH)
    )

    print(
        f"Linear Regression predictions saved: "
        f"{PREDICTIONS_OUTPUT_PATH}"
    )

    return metrics


def evaluate_random_forest(test_df):
    print("Evaluating Spark MLlib Random Forest...")

    print(
        f"Loading Random Forest model: "
        f"{RANDOM_FOREST_MODEL_PATH}"
    )

    model = RandomForestRegressionModel.load(
        str(RANDOM_FOREST_MODEL_PATH)
    )

    predictions = model.transform(test_df)

    metrics = calculate_metrics(predictions)

    print(f"Random Forest RMSE: {metrics['rmse']:.6f}")
    print(f"Random Forest MAE: {metrics['mae']:.6f}")
    print(f"Random Forest R²: {metrics['r2']:.6f}")

    predictions_output = predictions.select(
        TIME_COLUMN,
        TARGET_COLUMN,
        "prediction",
    )

    predictions_output.write.mode("overwrite").parquet(
        str(RANDOM_FOREST_PREDICTIONS_OUTPUT_PATH)
    )

    print(
        f"Random Forest predictions saved: "
        f"{RANDOM_FOREST_PREDICTIONS_OUTPUT_PATH}"
    )

    return metrics


def evaluate_model():
    spark = create_spark_session()

    try:
        print(f"Loading test dataset: {MLLIB_TEST_PATH}")

        test_df = spark.read.parquet(
            str(MLLIB_TEST_PATH)
        )

        validate_test_dataset(test_df)

        test_df = test_df.select(
            TIME_COLUMN,
            "features",
            TARGET_COLUMN,
        )

        test_rows = test_df.count()

        print(f"Test rows: {test_rows}")

        linear_regression_metrics = evaluate_linear_regression(
            test_df
        )

        random_forest_metrics = evaluate_random_forest(
            test_df
        )

        evaluation = {
            "framework": "Spark MLlib",
            "test_rows": test_rows,
            "models": {
                "linear_regression": {
                    "rmse": linear_regression_metrics["rmse"],
                    "mae": linear_regression_metrics["mae"],
                    "r2": linear_regression_metrics["r2"],
                },
                "random_forest": {
                    "rmse": random_forest_metrics["rmse"],
                    "mae": random_forest_metrics["mae"],
                    "r2": random_forest_metrics["r2"],
                },
            },
        }

        with open(
            EVALUATION_OUTPUT_PATH,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                evaluation,
                file,
                indent=2,
            )

        print(
            f"Evaluation saved: "
            f"{EVALUATION_OUTPUT_PATH}"
        )

        print("\nMLlib Model Comparison")
        print(
            f"Linear Regression | "
            f"RMSE: {linear_regression_metrics['rmse']:.6f} | "
            f"MAE: {linear_regression_metrics['mae']:.6f} | "
            f"R²: {linear_regression_metrics['r2']:.6f}"
        )
        print(
            f"Random Forest     | "
            f"RMSE: {random_forest_metrics['rmse']:.6f} | "
            f"MAE: {random_forest_metrics['mae']:.6f} | "
            f"R²: {random_forest_metrics['r2']:.6f}"
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    evaluate_model()