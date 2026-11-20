
from pathlib import Path

import pytest

from orchestration import cloud_storage


SKLEARN_CANDIDATE_ID = "c7f0d6784a6c4f1eaea121e510f606a5"
SPARK_CANDIDATE_ID = "980b37701e194ee0b3877bcaa555eed9"


def create_file(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("test artifact", encoding="utf-8")


def test_upload_sklearn_candidate(monkeypatch, tmp_path):
    candidate_dir = (
        tmp_path
        / "models"
        / "candidates"
        / SKLEARN_CANDIDATE_ID
    )

    required_files = [
        "linear_regression_model.pkl",
        "random_forest_model.pkl",
        "scaler.pkl",
    ]

    for filename in required_files:
        create_file(candidate_dir / filename)

    monkeypatch.setattr(
        cloud_storage,
        "W8_ROOT",
        tmp_path,
    )

    uploaded = []

    def mock_upload_file(local_file, s3_key, description):
        uploaded.append(s3_key)

    monkeypatch.setattr(
        cloud_storage,
        "upload_file",
        mock_upload_file,
    )

    cloud_storage.upload_sklearn_candidate(
        SKLEARN_CANDIDATE_ID
    )

    expected_prefix = (
        f"{cloud_storage.MLFLOW_S3_PREFIX}/candidates/sklearn/"
        f"{SKLEARN_CANDIDATE_ID}"
    )

    assert len(uploaded) == 3

    for filename in required_files:
        assert f"{expected_prefix}/{filename}" in uploaded


def test_upload_sklearn_candidate_rejects_invalid_id():
    with pytest.raises(ValueError):
        cloud_storage.upload_sklearn_candidate("invalid-id")


def test_upload_sklearn_candidate_detects_missing_files(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        cloud_storage,
        "W8_ROOT",
        tmp_path,
    )

    with pytest.raises(FileNotFoundError):
        cloud_storage.upload_sklearn_candidate(
            SKLEARN_CANDIDATE_ID
        )


def test_upload_spark_candidate(monkeypatch, tmp_path):
    candidate_models_dir = (
        tmp_path
        / "models"
        / "candidates"
        / SPARK_CANDIDATE_ID
    )

    model_dirs = [
        "mllib_linear_regression",
        "mllib_linear_regression_scaler",
        "mllib_random_forest",
    ]

    for model_name in model_dirs:
        create_file(
            candidate_models_dir
            / model_name
            / "metadata"
            / "test.txt"
        )

    candidate_test_dir = (
        tmp_path
        / "data"
        / "candidates"
        / SPARK_CANDIDATE_ID
        / "w7_mllib_test.parquet"
    )

    create_file(
        candidate_test_dir / "part-00000.parquet"
    )

    monkeypatch.setattr(
        cloud_storage,
        "P2_W7_ROOT",
        tmp_path,
    )

    uploaded = []

    def mock_upload_file(local_file, s3_key, description):
        uploaded.append(s3_key)

    monkeypatch.setattr(
        cloud_storage,
        "upload_file",
        mock_upload_file,
    )

    cloud_storage.upload_spark_candidate(
        SPARK_CANDIDATE_ID
    )

    expected_prefix = (
        f"{cloud_storage.MLFLOW_S3_PREFIX}/candidates/spark/"
        f"{SPARK_CANDIDATE_ID}"
    )

    assert any(
        f"{expected_prefix}/models/" in key
        for key in uploaded
    )

    assert any(
        f"{expected_prefix}/data/w7_mllib_test.parquet/"
        in key
        for key in uploaded
    )


def test_upload_spark_candidate_rejects_invalid_id():
    with pytest.raises(ValueError):
        cloud_storage.upload_spark_candidate("invalid-id")


def test_upload_spark_candidate_detects_missing_parquet(
    monkeypatch,
    tmp_path,
):
    candidate_models_dir = (
        tmp_path
        / "models"
        / "candidates"
        / SPARK_CANDIDATE_ID
    )

    for model_name in [
        "mllib_linear_regression",
        "mllib_linear_regression_scaler",
        "mllib_random_forest",
    ]:
        create_file(
            candidate_models_dir
            / model_name
            / "metadata"
            / "test.txt"
        )

    candidate_test_dir = (
        tmp_path
        / "data"
        / "candidates"
        / SPARK_CANDIDATE_ID
        / "w7_mllib_test.parquet"
    )

    create_file(candidate_test_dir / "test.txt")

    monkeypatch.setattr(
        cloud_storage,
        "P2_W7_ROOT",
        tmp_path,
    )

    with pytest.raises(FileNotFoundError):
        cloud_storage.upload_spark_candidate(
            SPARK_CANDIDATE_ID
        )


def test_production_upload_skips_candidate_models(
    monkeypatch,
    tmp_path,
):
    processed_dir = tmp_path / "data" / "processed"
    create_file(processed_dir / "processed.parquet")

    models_dir = tmp_path / "models"

    create_file(
        models_dir
        / "candidates"
        / SKLEARN_CANDIDATE_ID
        / "model.pkl"
    )

    create_file(
        models_dir
        / "mllib_linear_regression"
        / "model.txt"
    )

    monkeypatch.setattr(
        cloud_storage,
        "P2_W7_ROOT",
        tmp_path,
    )

    uploaded_prefixes = []

    def mock_upload_directory(
        local_dir,
        s3_prefix,
        replace=False,
    ):
        uploaded_prefixes.append(s3_prefix)

    monkeypatch.setattr(
        cloud_storage,
        "upload_directory",
        mock_upload_directory,
    )

    monkeypatch.setattr(
        cloud_storage,
        "upload_file",
        lambda *args, **kwargs: None,
    )

    cloud_storage.upload_p2_w7_artifacts()

    assert not any(
        "/candidates" in prefix
        for prefix in uploaded_prefixes
    )

    assert any(
        "mllib_linear_regression" in prefix
        for prefix in uploaded_prefixes
    )
