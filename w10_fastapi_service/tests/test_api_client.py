import requests
import pytest

from dashboard import api_client


class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self.json_data = json_data or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(
                f"HTTP {self.status_code}"
            )

    def json(self):
        return self.json_data


def test_request_prediction_success(monkeypatch):
    payload = {"temperature": 10.0}
    expected_url = "http://fastapi:8000/predict"

    monkeypatch.setattr(
        api_client,
        "API_URL",
        expected_url,
    )

    def mock_post(url, json, timeout):
        assert url == expected_url
        assert json == payload
        assert timeout == 10

        return MockResponse(
            json_data={"predicted_temperature": 12.5}
        )

    monkeypatch.setattr(
        api_client.requests,
        "post",
        mock_post,
    )

    result = api_client.request_prediction(payload)

    assert result == 12.5


def test_request_prediction_connection_failure(monkeypatch):
    def mock_post(*args, **kwargs):
        raise requests.exceptions.ConnectionError(
            "Connection refused"
        )

    monkeypatch.setattr(
        api_client.requests,
        "post",
        mock_post,
    )

    with pytest.raises(RuntimeError, match="Unable to connect"):
        api_client.request_prediction({"temperature": 10.0})


def test_request_prediction_missing_response_field(monkeypatch):
    monkeypatch.setattr(
        api_client.requests,
        "post",
        lambda *args, **kwargs: MockResponse(
            json_data={"status": "success"}
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="missing 'predicted_temperature'",
    ):
        api_client.request_prediction({"temperature": 10.0})


def test_check_api_health_success(monkeypatch):
    expected_url = "http://fastapi:8000/api"

    monkeypatch.setattr(
        api_client,
        "FASTAPI_URL",
        "http://fastapi:8000",
    )

    def mock_get(url, timeout):
        assert url == expected_url
        assert timeout == 5

        return MockResponse(status_code=200)

    monkeypatch.setattr(
        api_client.requests,
        "get",
        mock_get,
    )

    assert api_client.check_api_health() is True


def test_check_api_health_unhealthy_response(monkeypatch):
    monkeypatch.setattr(
        api_client.requests,
        "get",
        lambda *args, **kwargs: MockResponse(
            status_code=503
        ),
    )

    assert api_client.check_api_health() is False


def test_check_api_health_connection_failure(monkeypatch):
    def mock_get(*args, **kwargs):
        raise requests.exceptions.ConnectionError(
            "Connection refused"
        )

    monkeypatch.setattr(
        api_client.requests,
        "get",
        mock_get,
    )

    assert api_client.check_api_health() is False
