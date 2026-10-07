from pyspark.ml.regression import RandomForestRegressor
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.config import (
    MLLIB_TEST_PATH,
    MLLIB_TRAIN_PATH,
    RANDOM_FOREST_MAX_DEPTH,
    RANDOM_FOREST_MODEL_PATH,
    RANDOM_FOREST_NUM_TREES,
    RANDOM_SEED,
    SPARK_APP_NAME,
    SPARK_DRIVER_MEMORY,
    SPARK_MASTER,
    TARGET_COLUMN,
    TIME_COLUMN,
)


def create_spark_session():
    return (
        SparkSession.builder
        .appName(SPARK_APP_NAME)
        .master(SPARK_MASTER)
        .config("spark.driver.memory", SPARK_DRIVER_MEMORY)
        .getOrCreate()
    )


def train_random_forest():
    spark = create_spark_session()

    try:
        print(f"Loading training dataset: {MLLIB_TRAIN_PATH}")
        train_df = spark.read.parquet(str(MLLIB_TRAIN_PATH))

        print(f"Loading test dataset: {MLLIB_TEST_PATH}")
        test_df = spark.read.parquet(str(MLLIB_TEST_PATH))

        required_columns = [
            TIME_COLUMN,
            "features",
            TARGET_COLUMN,
        ]

        for name, df in [
            ("training", train_df),
            ("test", test_df),
        ]:
            missing_columns = [
                column
                for column in required_columns
                if column not in df.columns
            ]

            if missing_columns:
                raise ValueError(
                    f"Missing required columns in {name} dataset: "
                    f"{missing_columns}"
                )

        train_df = train_df.select(
            TIME_COLUMN,
            "features",
            TARGET_COLUMN,
        )

        test_df = test_df.select(
            TIME_COLUMN,
            "features",
            TARGET_COLUMN,
        )

        train_count = train_df.count()
        test_count = test_df.count()

        print(f"Training rows: {train_count}")
        print(f"Test rows: {test_count}")

        train_start = train_df.agg(
            F.min(TIME_COLUMN)
        ).first()[0]

        train_end = train_df.agg(
            F.max(TIME_COLUMN)
        ).first()[0]

        test_start = test_df.agg(
            F.min(TIME_COLUMN)
        ).first()[0]

        test_end = test_df.agg(
            F.max(TIME_COLUMN)
        ).first()[0]

        print(f"Training period: {train_start} → {train_end}")
        print(f"Test period: {test_start} → {test_end}")

        if train_end >= test_start:
            raise ValueError(
                "Chronological split validation failed: "
                "training period overlaps or reaches the test period."
            )

        print(
            "Training Spark MLlib Random Forest..."
        )

        model = RandomForestRegressor(
            featuresCol="features",
            labelCol=TARGET_COLUMN,
            predictionCol="prediction",
            numTrees=RANDOM_FOREST_NUM_TREES,
            maxDepth=RANDOM_FOREST_MAX_DEPTH,
            seed=RANDOM_SEED,
        )

        fitted_model = model.fit(train_df)

        fitted_model.write().overwrite().save(
            str(RANDOM_FOREST_MODEL_PATH)
        )

        print(
            f"Random Forest model saved: "
            f"{RANDOM_FOREST_MODEL_PATH}"
        )

        training_predictions = fitted_model.transform(train_df)

        rmse = (
            training_predictions
            .select(
                F.sqrt(
                    F.avg(
                        F.pow(
                            F.col("prediction")
                            - F.col(TARGET_COLUMN),
                            2,
                        )
                    )
                )
                .alias("rmse")
            )
            .first()["rmse"]
        )

        mae = (
            training_predictions
            .select(
                F.avg(
                    F.abs(
                        F.col("prediction")
                        - F.col(TARGET_COLUMN)
                    )
                )
                .alias("mae")
            )
            .first()["mae"]
        )

        print(f"Training RMSE: {rmse:.6f}")
        print(f"Training MAE: {mae:.6f}")
        print(f"Trees: {RANDOM_FOREST_NUM_TREES}")
        print(f"Max depth: {RANDOM_FOREST_MAX_DEPTH}")
        print(f"Random seed: {RANDOM_SEED}")

    finally:
        spark.stop()


if __name__ == "__main__":
    train_random_forest()