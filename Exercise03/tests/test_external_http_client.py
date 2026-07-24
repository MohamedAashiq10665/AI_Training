import httpx
import pytest

from app.domain.errors import ExternalAuthError, ExternalRateLimitError
from app.integrations.http_client import ResilientHttpClient


def test_client_retries_on_server_error_then_succeeds() -> None:
    call_count = {"value": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["value"] += 1
        if call_count["value"] == 1:
            return httpx.Response(503, json={"detail": "temporary"})
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    client = ResilientHttpClient(
        base_url="https://example.test",
        timeout_seconds=2.0,
        max_retries=2,
        backoff_seconds=0.0,
        transport=transport,
    )

    response = client.request_json("GET", "/sample")

    assert response["ok"] is True
    assert call_count["value"] == 2


def test_client_raises_auth_error_without_retry() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(401, json={"error": "unauthorized"}))
    client = ResilientHttpClient(
        base_url="https://example.test",
        timeout_seconds=2.0,
        max_retries=2,
        backoff_seconds=0.0,
        transport=transport,
    )

    with pytest.raises(ExternalAuthError):
        client.request_json("GET", "/auth")


def test_client_raises_rate_limit_after_retries() -> None:
    call_count = {"value": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["value"] += 1
        return httpx.Response(429, json={"error": "rate_limit"})

    transport = httpx.MockTransport(handler)
    client = ResilientHttpClient(
        base_url="https://example.test",
        timeout_seconds=2.0,
        max_retries=2,
        backoff_seconds=0.0,
        transport=transport,
    )

    with pytest.raises(ExternalRateLimitError):
        client.request_json("GET", "/limit")

    assert call_count["value"] == 3
