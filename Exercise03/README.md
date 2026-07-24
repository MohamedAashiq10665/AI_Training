# Exercise03 - Secure Third-Party Integration API

FastAPI service that manages customer data and enriches each customer profile with third-party data from:

- JSONPlaceholder (`https://jsonplaceholder.typicode.com`) for external customer activity
- OpenWeatherMap (`https://api.openweathermap.org`) for location-aware weather enrichment

This exercise demonstrates secure integration practices: secret management by environment variables, resilient retries, request timeouts, and robust external error handling.

## What Is Implemented

- In-memory customer API aligned with table reference entities:
  - `customers` (4 seeded records)
  - `customer_addresses`
  - `customer_business_profiles` (5 seeded records)
  - `tags`
  - `customer_tags`
- Third-party enrichment endpoint:
  - `GET /customers/{customer_id}/enriched-profile`
- Secure config:
  - API secrets/tokens are read only from environment variables
- Resilience:
  - retry with exponential backoff for transient failures
  - timeout handling for slow upstreams
  - external auth/rate-limit/server error mapping
- Tests:
  - unit and API tests with mocked external providers
  - HTTP client retry/error tests using `httpx.MockTransport`

## Project Structure

```text
Exercise03/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── customers.py
│   │       └── tags.py
│   ├── core/
│   │   └── config.py
│   ├── domain/
│   │   └── errors.py
│   ├── integrations/
│   │   ├── http_client.py
│   │   └── providers/
│   │       ├── interfaces.py
│   │       ├── jsonplaceholder_client.py
│   │       └── openweather_client.py
│   ├── models/
│   │   └── schemas.py
│   ├── repositories/
│   │   └── mock_db.py
│   ├── services/
│   │   └── customer_service.py
│   └── main.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_customer_service.py
│   └── test_external_http_client.py
└── requirements.txt
```

## Environment Variables

Required for weather enrichment:

- `OPENWEATHER_API_KEY`

Optional:

- `JSONPLACEHOLDER_BEARER_TOKEN` (demonstrates outbound bearer-token handling)
- `EXTERNAL_TIMEOUT_SECONDS` (default: `5.0`)
- `EXTERNAL_MAX_RETRIES` (default: `2`)
- `EXTERNAL_BACKOFF_SECONDS` (default: `0.25`)

PowerShell example:

```powershell
$env:OPENWEATHER_API_KEY = "your-api-key"
$env:JSONPLACEHOLDER_BEARER_TOKEN = "optional-token"
$env:EXTERNAL_TIMEOUT_SECONDS = "5.0"
$env:EXTERNAL_MAX_RETRIES = "2"
$env:EXTERNAL_BACKOFF_SECONDS = "0.25"
```

## Run Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Docs URL:

- `http://127.0.0.1:8000/docs`

## Integration Flow

1. Load internal customer details from the local repository.
2. Request activity summary from JSONPlaceholder (`/users/{id}/todos` and `/users/{id}/posts`).
3. Resolve customer address coordinates via OpenWeatherMap geocoding.
4. Request current weather using coordinates.
5. Return a single enriched payload.
6. If external systems fail, return partial data with `warnings` (graceful degradation).

## Request/Response Formats

### Enriched Customer Profile

Request:

- `GET /customers/{customer_id}/enriched-profile?include_activity=true&include_weather=true`

Sample response:

```json
{
  "customer": {
    "customer_id": 1,
    "first_name": "Ava",
    "last_name": "Stone",
    "email": "ava.stone@example.com",
    "phone": "+1-555-1000",
    "status": "Active",
    "customer_type": "B2C",
    "created_at": "2026-07-24T10:00:00.000000Z",
    "updated_at": "2026-07-24T10:00:00.000000Z",
    "addresses": [],
    "business_profiles": [],
    "tags": []
  },
  "external_activity": {
    "open_todos": 2,
    "total_todos": 5,
    "recent_post_titles": [
      "Update for user 1",
      "Invoice follow-up",
      "Shipping note"
    ]
  },
  "weather": {
    "provider": "openweathermap",
    "city": "Austin",
    "temperature_c": 31.5,
    "condition": "Clear",
    "wind_speed_mps": 4.1
  },
  "warnings": [],
  "retrieved_at": "2026-07-24T10:00:00.000000Z"
}
```

## Security Considerations

- No secrets are hardcoded in source files.
- API keys/tokens are loaded from process environment at startup.
- Upstream auth errors and rate limits are handled explicitly.
- Error messages returned by the API avoid exposing secret values.
- Timeout and retry policies reduce risk of hanging requests and transient outage impact.

## Error Handling and Retry Strategy

Implemented in `ResilientHttpClient`:

- Retries (`EXTERNAL_MAX_RETRIES`) for:
  - `429`
  - `500`, `502`, `503`, `504`
  - network errors and timeouts
- Exponential backoff using `EXTERNAL_BACKOFF_SECONDS * 2^attempt`
- Auth errors (`401`, `403`) fail fast as external auth failures

## Testing

Run:

```bash
pytest
```

Test coverage includes:

- API behavior for CRUD + enrichment endpoint
- service-level business rules
- mocked external provider usage (`unittest.mock.Mock`)
- retry/auth/rate-limit behavior in HTTP client with mocked transport

## Copilot Usage Demonstrated

This exercise is designed to show practical Copilot-assisted workflows for:

- generating SDK/HTTP integration scaffolding
- producing consistent retry/timeout/error handling patterns
- creating mocked tests for external integrations
- documenting secure configuration and API contracts
