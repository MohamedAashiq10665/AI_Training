# Customer Details CRUD API

RESTful CRUD API for managing customer data with in-memory mock storage. The project uses FastAPI for the API layer and pytest for unit tests.

## Features

- CRUD for customers
- CRUD for customer addresses
- CRUD for customer business profiles
- CRUD for tags
- Assign and remove tags from customers
- Validation for duplicate customer emails
- Validation for foreign keys such as `customer_id` and `tag_id`
- Swagger UI from FastAPI at `/docs`

## Project Structure

```text
Exercise01/
├── app/
│   ├── api/
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── customers.py
│   │       └── tags.py
│   ├── domain/
│   │   └── errors.py
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
│   └── test_customer_service.py
└── requirements.txt
```

## Assumptions

- All data is mock data kept in memory and reset whenever the app restarts.
- `email` must be unique across customers.
- `customer_id` must exist before an address, business profile, or customer-tag relationship can be created.
- Deleting a customer cascades to addresses, business profiles, and customer-tag mappings.
- One customer may have multiple addresses and multiple business profiles.
- Setting an address as primary clears the `is_primary` flag from the same customer's other addresses.

## Run Locally

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the API:

```bash
uvicorn app.main:app --reload
```

4. Open the docs:

```text
http://127.0.0.1:8000/docs
```

## Run Tests

```bash
pytest
```

## Main Endpoints

### Customers

- `GET /customers`
- `POST /customers`
- `GET /customers/{customer_id}`
- `PUT /customers/{customer_id}`
- `DELETE /customers/{customer_id}`
- `GET /customers/{customer_id}/details`

### Customer Addresses

- `GET /customers/{customer_id}/addresses`
- `POST /customers/{customer_id}/addresses`
- `GET /customers/addresses/{address_id}`
- `PUT /customers/addresses/{address_id}`
- `DELETE /customers/addresses/{address_id}`

### Customer Business Profiles

- `GET /customers/{customer_id}/business-profiles`
- `POST /customers/{customer_id}/business-profiles`
- `GET /customers/business-profiles/{business_profile_id}`
- `PUT /customers/business-profiles/{business_profile_id}`
- `DELETE /customers/business-profiles/{business_profile_id}`

### Tags

- `GET /tags`
- `POST /tags`
- `GET /tags/{tag_id}`
- `PUT /tags/{tag_id}`
- `DELETE /tags/{tag_id}`
- `GET /customers/{customer_id}/tags`
- `POST /customers/{customer_id}/tags/{tag_id}`
- `DELETE /customers/{customer_id}/tags/{tag_id}`

## GitHub Copilot Usage

This implementation is structured to demonstrate Copilot-assisted scaffolding for:

- Project layout and boilerplate setup
- CRUD route generation
- Service-layer unit tests
- README and endpoint documentation
