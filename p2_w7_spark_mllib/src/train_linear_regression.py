from pyspark.ml.feature import StandardScaler
from pyspark.ml.regression import LinearRegression
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

from src.config import (
    LINEAR_REGRESSION_MAX_ITER,
    LINEAR_REGRESSION_MODEL_PATH,
    MLLIB_FEATURES_PATH,
    MLLIB_TEST_PATH,
    MLLIB_TRAIN_PATH,
    RANDOM_SEED,
    SPARK_APP_NAME,
    SPARK_DRIVER_MEMORY,
    SPARK_MASTER,
    TARGET_COLUMN,
    TIME_COLUMN,
)


TRAIN_RATIO = 0.80
SCALER_MODEL_PATH = LINEAR_REGRESSION_MODEL_PATH.parent / "mllib_linear_regression_scaler"


def create_spark_session():
    return (
        SparkSession.builder
        .appName(SPARK_APP_NAME)
        .master(SPARK_MASTER)
        .config("spark.driver.memory", SPARK_DRIVER_MEMORY)
        .getOrCreate()
    )


def create_chronological_split(df):
    timestamps = (
        df
        .select(TIME_COLUMN)
        .distinct()
        .orderBy(F.col(TIME_COLUMN))
    )

    total_timestamps = timestamps.count()
    train_timestamps = int(total_timestamps * TRAIN_RATIO)

    if train_timestamps <= 0 or train_timestamps >= total_timestamps:
        raise ValueError(
            f"Invalid chronological split: "
            f"total_timestamps={total_timestamps}, "
            f"train_timestamps={train_timestamps}"
        )

    train_timestamp_df = timestamps.limit(train_timestamps)

    test_timestamp_df = (
        timestamps
        .subtract(train_timestamp_df)
        .orderBy(F.col(TIME_COLUMN))
    )

    train_df = df.join(
        train_timestamp_df,
        on=TIME_COLUMN,
        how="inner",
    )

    test_df = df.join(
        test_timestamp_df,
        on=TIME_COLUMN,
        how="inner",
    )

    return (
        train_df.orderBy(F.col(TIME_COLUMN)),
        test_df.orderBy(F.col(TIME_COLUMN)),
    )


def train_linear_regression():
    spark = create_spark_session()

    try:
        print(f"Loading MLlib feature dataset: {MLLIB_FEATURES_PATH}")

        df = spark.read.parquet(str(MLLIB_FEATURES_PATH))

        required_columns = [
            TIME_COLUMN,
            "features",
            TARGET_COLUMN,
        ]

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}"
            )

        df = df.select(
            TIME_COLUMN,
            "features",
            TARGET_COLUMN,
        )

        total_rows = df.count()

        print(f"Total rows: {total_rows}")

        train_df, test_df = create_chronological_split(df)

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

        train_df.write.mode("overwrite").parquet(
            str(MLLIB_TRAIN_PATH)
        )

        test_df.write.mode("overwrite").parquet(
            str(MLLIB_TEST_PATH)
        )

        print(f"Training dataset saved: {MLLIB_TRAIN_PATH}")
        print(f"Test dataset saved: {MLLIB_TEST_PATH}")

        scaler = StandardScaler(
            inputCol="features",
            outputCol="scaled_features",
            withStd=True,
            withMean=False,
        )

        print("Fitting StandardScaler on training data...")

        scaler_model = scaler.fit(train_df)

        scaler_model.write().overwrite().save(
            str(SCALER_MODEL_PATH)
        )

        print(
            f"StandardScaler model saved: "
            f"{SCALER_MODEL_PATH}"
        )

        train_scaled = scaler_model.transform(train_df)

        train_scaled = (
            train_scaled
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

        model = LinearRegression(
            featuresCol="features",
            labelCol=TARGET_COLUMN,
            predictionCol="prediction",
            maxIter=LINEAR_REGRESSION_MAX_ITER,
            regParam=0.0,
            elasticNetParam=0.0,
        )

        print("Training Spark MLlib Linear Regression...")

        fitted_model = model.fit(train_scaled)

        fitted_model.write().overwrite().save(
            str(LINEAR_REGRESSION_MODEL_PATH)
        )

        print(
            f"Linear Regression model saved: "
            f"{LINEAR_REGRESSION_MODEL_PATH}"
        )

        print(
            f"Iterations: "
            f"{fitted_model.summary.totalIterations}"
        )

        print(
            f"Training RMSE: "
            f"{fitted_model.summary.rootMeanSquaredError:.6f}"
        )

        print(
            f"Training MAE: "
            f"{fitted_model.summary.meanAbsoluteError:.6f}"
        )

        print(
            f"Training R²: "
            f"{fitted_model.summary.r2:.6f}"
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    train_linear_regression()