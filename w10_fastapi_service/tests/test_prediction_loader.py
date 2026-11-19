import pandas as pd
import pytest

from dashboard import prediction_loader


@pytest.fixture
def prediction_csv(tmp_path, monkeypatch):
    """Create a temporary prediction dataset."""

    today = pd.Timestamp.now().normalize()
    yesterday = today - pd.Timedelta(days=1)

    df = pd.DataFrame({
        "time": [
            yesterday,
            yesterday + pd.Timedelta(hours=1),
            yesterday + pd.Timedelta(hours=2),
            today,
        ],
        "city_London": [0, 1, 0, 0],
        "city_Manchester": [0, 0, 1, 0],
        "target_temp_next_hour": [10.0, 12.0, 11.0, 9.0],
        "predicted_temperature": [10.2, 11.8, 11.1, 9.2],
        "prediction_error": [-0.2, 0.2, -0.1, -0.2],
    })

    file_path = tmp_path / "weather_predictions.csv"
    df.to_csv(file_path, index=False)

    monkeypatch.setattr(
        prediction_loader,
        "PREDICTION_FILE",
        file_path,
    )

    return yesterday


def test_load_prediction_data(prediction_csv):
    df = prediction_loader.load_prediction_data()

    assert not df.empty
    assert pd.api.types.is_datetime64_any_dtype(df["time"])
    assert "city" in df.columns
    assert len(df) == 3


def test_reconstruct_city_names(prediction_csv):
    df = prediction_loader.load_prediction_data()

    assert set(df["city"]) == {
        "Edinburgh",
        "London",
        "Manchester",
    }


def test_exclude_current_day_predictions(prediction_csv):
    df = prediction_loader.load_prediction_data()

    assert all(
        df["time"].dt.date < pd.Timestamp.now().date()
    )


def test_filter_prediction_data_by_city_and_date(prediction_csv):
    df = prediction_loader.load_prediction_data()

    selected_date = prediction_csv.strftime("%Y-%m-%d")

    filtered = prediction_loader.filter_prediction_data(
        df,
        "London",
        selected_date,
    )

    assert len(filtered) == 1
    assert filtered.iloc[0]["city"] == "London"


def test_missing_prediction_file(tmp_path, monkeypatch):
    missing_file = tmp_path / "missing.csv"

    monkeypatch.setattr(
        prediction_loader,
        "PREDICTION_FILE",
        missing_file,
    )

    with pytest.raises(FileNotFoundError):
        prediction_loader.load_prediction_data()
