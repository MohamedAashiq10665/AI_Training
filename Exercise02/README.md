# Customer Details CRUD API (Database-Backed)

RESTful CRUD API for managing customer data using FastAPI + SQLAlchemy with a SQLite database.

## What Changed

- Replaced in-memory storage with persistent relational storage (SQLite by default).
- Added a dedicated repository/DAO abstraction: service layer no longer accesses storage directly.
- Added stricter validations:
	- `first_name` and `last_name`: min 2, max 50 characters.
	- `onboarding_date` must be greater than `establishment_start_date`.
- Added both:
	- unit tests with mocked repository (`tests/test_customer_service.py`)
	- integration tests using a real SQLite database (`tests/test_api.py` + fixture in `tests/conftest.py`)

## Architecture

- API routes: `app/api/routes/*`
- Service layer: `app/services/customer_service.py`
- Repository/DAO layer: `app/repositories/customer_repository.py`
- ORM entities: `app/models/db_models.py`
- DB setup/session management: `app/db/database.py`
- App config from environment variables: `app/core/config.py`

## Database Configuration

The app reads DB connection from environment variable:

- `DATABASE_URL`

Default value when not provided:

```text
sqlite:///./customer_details.db
```

Examples:

```bash
# Windows PowerShell
$env:DATABASE_URL="sqlite:///./customer_details.db"

# PostgreSQL example
$env:DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/customer_db"
```

## Schema Summary

- `customers`
	- `customer_id` (PK)
	- `first_name`, `last_name`, `email` (unique), `phone`
	- `status`, `customer_type`, `created_at`, `updated_at`
- `customer_addresses`
	- `address_id` (PK), `customer_id` (FK)
	- address fields + `is_primary`
- `customer_business_profiles`
	- `business_profile_id` (PK), `customer_id` (FK)
	- `company_name`, `job_title`, `lead_source`, `lifecycle_stage`
	- `establishment_start_date`, `onboarding_date`
- `tags`
	- `tag_id` (PK), `tag_name` (unique)
- `customer_tags`
	- relation table between customers and tags
	- unique `(customer_id, tag_id)`

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Optionally configure `DATABASE_URL`.
4. Start API:

```bash
uvicorn app.main:app --reload
```

5. Open docs:

```text
http://127.0.0.1:8000/docs
```

## Testing

Run all tests:

```bash
pytest
```

- Unit tests mock DAO/repository interactions.
- Integration tests spin up an isolated SQLite database per test.

## Copilot Usage Notes

This exercise intentionally demonstrates effective Copilot-assisted workflows for:

- SQLAlchemy model and relationship scaffolding
- DAO/repository method generation
- query and serialization helpers
- test fixture and integration test scaffolding
