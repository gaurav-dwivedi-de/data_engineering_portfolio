from pyspark.ml.feature import VectorAssembler
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

from src.config import (
    MLLIB_CLEAN_PATH,
    MLLIB_FEATURES_PATH,
    MLLIB_INPUT_PATH,
    SPARK_APP_NAME,
    SPARK_DRIVER_MEMORY,
    SPARK_MASTER,
    TARGET_COLUMN,
    TIME_COLUMN,
    W7_FEATURE_DATA_PATH,
)


FEATURE_COLUMNS = [
    "temperature",
    "humidity",
    "windspeed",
    "year",
    "month",
    "day",
    "hour",
    "day_of_week",
    "week_of_year",
    "day_of_year",
    "is_weekend",
    "temp_rolling_mean",
    "humidity_rolling_mean",
    "windspeed_rolling_mean",
    "temp_lag_1",
    "temp_lag_3",
    "humidity_lag_1",
    "windspeed_lag_1",
    "temp_delta",
    "humidity_delta",
    "windspeed_delta",
    "temp_pct_change",
    "humidity_pct_change",
    "windspeed_pct_change",
    "city_London",
    "city_Manchester",
    "source_forecast",
]


def create_spark_session():
    return (
        SparkSession.builder
        .appName(SPARK_APP_NAME)
        .master(SPARK_MASTER)
        .config("spark.driver.memory", SPARK_DRIVER_MEMORY)
        .getOrCreate()
    )


def create_spark_compatible_input(spark):
    import pyarrow as pa
    import pyarrow.parquet as pq

    print(f"Loading W7 feature dataset: {W7_FEATURE_DATA_PATH}")

    table = pq.read_table(str(W7_FEATURE_DATA_PATH))

    schema = table.schema

    fields = []

    for field in schema:
        if pa.types.is_timestamp(field.type):
            fields.append(
                pa.field(
                    field.name,
                    pa.timestamp("us"),
                    nullable=field.nullable,
                )
            )
        else:
            fields.append(field)

    compatible_schema = pa.schema(fields)

    table = table.cast(compatible_schema)

    pq.write_table(
        table,
        str(MLLIB_INPUT_PATH),
    )

    print(f"Spark-compatible input saved: {MLLIB_INPUT_PATH}")

    df = spark.read.parquet(str(MLLIB_INPUT_PATH))

    print(f"Spark-compatible rows: {df.count()}")

    return df


def create_clean_dataset(df):
    partition_columns = [
        "city_London",
        "city_Manchester",
    ]

    window = (
        Window
        .partitionBy(*partition_columns)
        .orderBy(F.col(TIME_COLUMN))
    )

    total_rows_window = window.rowsBetween(
        Window.unboundedPreceding,
        Window.unboundedFollowing,
    )

    df = (
        df
        .withColumn("_row_number", F.row_number().over(window))
        .withColumn("_total_rows", F.count("*").over(total_rows_window))
    )

    clean_df = (
        df
        .filter(
            (F.col("_row_number") > 3)
            & (F.col("_row_number") <= F.col("_total_rows") - 1)
        )
        .drop("_row_number", "_total_rows")
    )

    return clean_df


def create_feature_vector(df):
    missing_columns = [
        column
        for column in FEATURE_COLUMNS + [TIME_COLUMN, TARGET_COLUMN]
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns for MLlib feature preparation: "
            f"{missing_columns}"
        )

    assembler = VectorAssembler(
        inputCols=FEATURE_COLUMNS,
        outputCol="features",
        handleInvalid="error",
    )

    feature_df = assembler.transform(df)

    return feature_df.select(
        TIME_COLUMN,
        "features",
        TARGET_COLUMN,
    )


def prepare_data():
    spark = create_spark_session()

    try:
        df = create_spark_compatible_input(spark)

        clean_df = create_clean_dataset(df)

        print(f"Clean rows: {clean_df.count()}")

        clean_df.write.mode("overwrite").parquet(
            str(MLLIB_CLEAN_PATH)
        )

        print(f"Clean dataset saved: {MLLIB_CLEAN_PATH}")

        feature_df = create_feature_vector(clean_df)

        print(f"MLlib feature rows: {feature_df.count()}")

        feature_df.write.mode("overwrite").parquet(
            str(MLLIB_FEATURES_PATH)
        )

        print(f"MLlib feature dataset saved: {MLLIB_FEATURES_PATH}")

    finally:
        spark.stop()


if __name__ == "__main__":
    prepare_data()