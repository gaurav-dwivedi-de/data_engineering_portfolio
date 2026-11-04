import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = Path(
    os.getenv(
        "W7_FEATURE_DATA_PATH",
        str(
            PROJECT_ROOT
            / "w7_feature_engineering"
            / "data"
            / "processed"
            / "w7_features_final.parquet"
        ),
    )
)

TARGET_COLUMN = "target_temp_next_hour"
TIME_COLUMN = "time"
TEST_SIZE = 0.2
RANDOM_STATE = 42

DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV")

if DEPLOYMENT_ENV not in {"dev", "prod"}:
    raise RuntimeError(
        "DEPLOYMENT_ENV must be configured as 'dev' or 'prod'."
    )

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")

if not MLFLOW_TRACKING_URI:
    raise RuntimeError("MLFLOW_TRACKING_URI is not configured.")

MLFLOW_EXPERIMENT_NAME = os.getenv(
    "MLFLOW_EXPERIMENT_NAME",
    f"weather-intelligence-model-comparison-{DEPLOYMENT_ENV}",
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