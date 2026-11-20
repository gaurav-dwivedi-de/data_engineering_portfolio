
from pathlib import Path

import pytest

from mlflow_integration.src import evaluate_models


SKLEARN_ID = "c7f0d6784a6c4f1eaea121e510f606a5"
SPARK_ID = "980b37701e194ee0b3877bcaa555eed9"


def test_download_candidate_artifacts(monkeypatch, tmp_path):
    project_root = tmp_path

    w8_dir = project_root / "w8"
    spark_dir = project_root / "p2_w7_spark_mllib"

    w8_dir.mkdir()
    spark_dir.mkdir()

    monkeypatch.setattr(
        evaluate_models,
        "PROJECT_ROOT",
        project_root,
    )

    client_calls = []

    def mock_boto3_client(service, region_name=None):
        client_calls.append((service, region_name))
        return object()

    monkeypatch.setattr(
        evaluate_models.boto3,
        "client",
        mock_boto3_client,
    )

    downloads = []

    def mock_download_prefix(s3, prefix, destination):
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)

        downloads.append((prefix, destination))

        (destination / "test_artifact.txt").write_text(
            "test artifact",
            encoding="utf-8",
        )

        return 1

    monkeypatch.setattr(
        evaluate_models,
        "download_prefix",
        mock_download_prefix,
    )

    evaluate_models.download_candidate_artifacts(
        sklearn_candidate_run_id=SKLEARN_ID,
        spark_candidate_run_id=SPARK_ID,
    )

    expected_downloads = {
        (
            f"{evaluate_models.MLFLOW_S3_PREFIX}/candidates/"
            f"sklearn/{SKLEARN_ID}/",
            w8_dir / "models" / "candidates" / SKLEARN_ID,
        ),
        (
            f"{evaluate_models.MLFLOW_S3_PREFIX}/candidates/"
            f"spark/{SPARK_ID}/models/",
            spark_dir / "models" / "candidates" / SPARK_ID,
        ),
        (
            f"{evaluate_models.MLFLOW_S3_PREFIX}/candidates/"
            f"spark/{SPARK_ID}/data/w7_mllib_test.parquet/",
            spark_dir
            / "data"
            / "candidates"
            / SPARK_ID
            / "w7_mllib_test.parquet",
        ),
    }

    assert set(downloads) == expected_downloads

    assert len(downloads) == 3
    assert len(client_calls) == 1
    assert client_calls[0][0] == "s3"

    for _, destination in downloads:
        assert (destination / "test_artifact.txt").is_file()


@pytest.mark.parametrize(
    ("sklearn_id", "spark_id"),
    [
        ("invalid-id", SPARK_ID),
        (SKLEARN_ID, "invalid-id"),
        ("", SPARK_ID),
        (SKLEARN_ID, ""),
    ],
)
def test_download_candidate_artifacts_rejects_invalid_ids(
    monkeypatch,
    sklearn_id,
    spark_id,
):
    def unexpected_call(*args, **kwargs):
        pytest.fail("S3 client should not be created for invalid IDs")

    monkeypatch.setattr(
        evaluate_models.boto3,
        "client",
        unexpected_call,
    )

    with pytest.raises(ValueError):
        evaluate_models.download_candidate_artifacts(
            sklearn_candidate_run_id=sklearn_id,
            spark_candidate_run_id=spark_id,
        )


def test_download_candidate_artifacts_preserves_other_candidates(
    monkeypatch,
    tmp_path,
):
    project_root = tmp_path

    w8_dir = project_root / "w8"
    spark_dir = project_root / "p2_w7_spark_mllib"

    w8_dir.mkdir()
    spark_dir.mkdir()

    monkeypatch.setattr(
        evaluate_models,
        "PROJECT_ROOT",
        project_root,
    )

    current_candidate = (
        w8_dir / "models" / "candidates" / SKLEARN_ID
    )
    other_candidate = (
        w8_dir / "models" / "candidates" / "another_candidate"
    )

    current_candidate.mkdir(parents=True)
    other_candidate.mkdir(parents=True)

    (current_candidate / "old.txt").write_text("old")
    (other_candidate / "keep.txt").write_text("keep")

    monkeypatch.setattr(
        evaluate_models.boto3,
        "client",
        lambda *args, **kwargs: object(),
    )

    def mock_download_prefix(s3, prefix, destination):
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)

        (destination / "downloaded.txt").write_text(
            "downloaded",
            encoding="utf-8",
        )

        return 1

    monkeypatch.setattr(
        evaluate_models,
        "download_prefix",
        mock_download_prefix,
    )

    evaluate_models.download_candidate_artifacts(
        sklearn_candidate_run_id=SKLEARN_ID,
        spark_candidate_run_id=SPARK_ID,
    )

    assert not (current_candidate / "old.txt").exists()
    assert (current_candidate / "downloaded.txt").exists()

    assert (other_candidate / "keep.txt").exists()


def test_download_prefix_restores_nested_files(tmp_path):
    prefix = "mlflow/candidates/test/"

    objects = [
        {"Key": f"{prefix}model.pkl"},
        {"Key": f"{prefix}metadata/part-00000"},
        {"Key": f"{prefix}metadata/"},
    ]

    class FakePaginator:
        def paginate(self, **kwargs):
            assert kwargs["Prefix"] == prefix
            return [{"Contents": objects}]

    class FakeS3:
        def get_paginator(self, operation):
            assert operation == "list_objects_v2"
            return FakePaginator()

        def download_file(self, bucket, key, destination):
            target = Path(destination)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                f"downloaded {key}",
                encoding="utf-8",
            )

    destination = tmp_path / "candidate"

    count = evaluate_models.download_prefix(
        FakeS3(),
        prefix,
        destination,
    )

    assert count == 2
    assert (destination / "model.pkl").is_file()
    assert (
        destination / "metadata" / "part-00000"
    ).is_file()


def test_download_prefix_raises_when_no_objects_exist(tmp_path):
    class FakePaginator:
        def paginate(self, **kwargs):
            return [{"Contents": []}]

    class FakeS3:
        def get_paginator(self, operation):
            return FakePaginator()

    with pytest.raises(FileNotFoundError):
        evaluate_models.download_prefix(
            FakeS3(),
            "mlflow/candidates/missing/",
            tmp_path / "missing",
        )
