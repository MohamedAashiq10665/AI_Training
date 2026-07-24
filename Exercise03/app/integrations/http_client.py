import time

import httpx

from app.domain.errors import ExternalAuthError, ExternalRateLimitError, ExternalServiceError


class ResilientHttpClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        max_retries: int,
        backoff_seconds: float,
        default_headers: dict[str, str] | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.default_headers = default_headers or {}
        self._client = httpx.Client(base_url=self.base_url, transport=transport)

    def request_json(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict | list:
        merged_headers = {**self.default_headers, **(headers or {})}

        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.request(
                    method=method,
                    url=path,
                    params=params,
                    headers=merged_headers,
                    timeout=self.timeout_seconds,
                )

                if response.status_code in (401, 403):
                    raise ExternalAuthError("External API authentication failed.")

                if response.status_code == 429:
                    if attempt < self.max_retries:
                        self._backoff(attempt)
                        continue
                    raise ExternalRateLimitError("External API rate limit exceeded.")

                if response.status_code in (500, 502, 503, 504):
                    if attempt < self.max_retries:
                        self._backoff(attempt)
                        continue
                    raise ExternalServiceError(
                        f"External API remained unavailable after retries (status={response.status_code})."
                    )

                if response.status_code >= 400:
                    raise ExternalServiceError(
                        f"External API returned an unexpected error (status={response.status_code})."
                    )

                if not response.content:
                    return {}
                return response.json()
            except (httpx.TimeoutException, httpx.RequestError) as error:
                if attempt < self.max_retries:
                    self._backoff(attempt)
                    continue
                raise ExternalServiceError("External API request failed due to a network or timeout error.") from error

        raise ExternalServiceError("External API request failed unexpectedly.")

    def _backoff(self, attempt: int) -> None:
        delay = self.backoff_seconds * (2**attempt)
        time.sleep(delay)

    def close(self) -> None:
        self._client.close()
