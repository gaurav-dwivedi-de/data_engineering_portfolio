import os
from pathlib import Path



# Project Root


PROJECT_ROOT = Path(__file__).resolve().parents[2]



# Environment Detection


AIRFLOW_ROOT = Path("/opt/airflow")

if AIRFLOW_ROOT.exists():
    PORTFOLIO_ROOT = AIRFLOW_ROOT
    W7_FOLDER = "w7"
else:
    PORTFOLIO_ROOT = PROJECT_ROOT
    W7_FOLDER = "w7_feature_engineering"



# Week 7 Feature Dataset


DEFAULT_W7_FEATURE_DATA_PATH = (
    PORTFOLIO_ROOT
    / W7_FOLDER
    / "data"
    / "processed"
    / "w7_features_final.parquet"
)

W7_FEATURE_DATA_PATH = Path(
    os.getenv(
        "W7_FEATURE_DATA_PATH",
        str(DEFAULT_W7_FEATURE_DATA_PATH),
    )
)


# P2-W7 Data Directories


DATA_DIR = (
    PROJECT_ROOT
    / "data"
)

PROCESSED_DATA_DIR = (
    DATA_DIR
    / "processed"
)

FIGURES_DIR = (
    PROJECT_ROOT
    / "figures"
)

MODELS_DIR = (
    PROJECT_ROOT
    / "models"
)

# Spark-Compatible Dataset


MLLIB_INPUT_PATH = (
    PROCESSED_DATA_DIR
    / "w7_mllib_input.parquet"
)

MLLIB_CLEAN_PATH = (
    PROCESSED_DATA_DIR
    / "w7_mllib_clean.parquet"
)

MLLIB_FEATURES_PATH = (
    PROCESSED_DATA_DIR
    / "w7_mllib_features.parquet"
)

# Train / Test Datasets


MLLIB_TRAIN_PATH = (
    PROCESSED_DATA_DIR
    / "w7_mllib_train.parquet"
)

MLLIB_TEST_PATH = (
    PROCESSED_DATA_DIR
    / "w7_mllib_test.parquet"
)

# MLlib Models

LINEAR_REGRESSION_MODEL_PATH = (
    MODELS_DIR
    / "mllib_linear_regression"
)

RANDOM_FOREST_MODEL_PATH = (
    MODELS_DIR
    / "mllib_random_forest"
)



# Evaluation Output


EVALUATION_OUTPUT_PATH = (
    PROCESSED_DATA_DIR
    / "w7_mllib_evaluation.json"
)

PREDICTIONS_OUTPUT_PATH = (
    PROCESSED_DATA_DIR
    / "w7_mllib_predictions.parquet"
)

# Dataset Columns

TIME_COLUMN = "time"

TARGET_COLUMN = "target_temp_next_hour"

# Spark Configuration

SPARK_APP_NAME = os.getenv(
    "SPARK_APP_NAME",
    "weather-intelligence-p2-w7-mllib",
)

SPARK_MASTER = os.getenv(
    "SPARK_MASTER",
    "local[*]",
)

SPARK_DRIVER_MEMORY = os.getenv(
    "SPARK_DRIVER_MEMORY",
    "4g",
)



# MLlib Configuration


RANDOM_SEED = 42

LINEAR_REGRESSION_MAX_ITER = 100

RANDOM_FOREST_NUM_TREES = 100

RANDOM_FOREST_MAX_DEPTH = 5



# Create Required Directories


PROCESSED_DATA_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

FIGURES_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

MODELS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)