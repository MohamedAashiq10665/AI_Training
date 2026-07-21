from fastapi.testclient import TestClient


def test_create_customer_returns_201(client: TestClient) -> None:
    response = client.post(
        "/customers",
        json={
            "first_name": "Lina",
            "last_name": "Harper",
            "email": "lina.harper@example.com",
            "phone": "+1-555-3000",
            "status": "Active",
            "customer_type": "B2C",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["customer_id"] == 1
    assert body["email"] == "lina.harper@example.com"


def test_create_address_for_missing_customer_returns_404(client: TestClient) -> None:
    response = client.post(
        "/customers/999/addresses",
        json={
            "address_type": "Shipping",
            "address_line1": "15 Harbor Road",
            "city": "Seattle",
            "state_province": "WA",
            "postal_code": "98101",
            "country_code": "US",
            "is_primary": True,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer 999 was not found."


def test_assign_duplicate_tag_returns_409(client: TestClient) -> None:
    customer_response = client.post(
        "/customers",
        json={
            "first_name": "Ari",
            "last_name": "Baker",
            "email": "ari.baker@example.com",
            "status": "Active",
            "customer_type": "B2B",
        },
    )
    customer_id = customer_response.json()["customer_id"]
    tag_response = client.post("/tags", json={"tag_name": "vip"})
    tag_id = tag_response.json()["tag_id"]

    first_assign = client.post(f"/customers/{customer_id}/tags/{tag_id}")
    assert first_assign.status_code == 200

    response = client.post(f"/customers/{customer_id}/tags/{tag_id}")

    assert response.status_code == 409
    assert response.json()["detail"] == f"Tag {tag_id} is already assigned to customer {customer_id}."


def test_get_customer_details_returns_nested_data(client: TestClient) -> None:
    customer = client.post(
        "/customers",
        json={
            "first_name": "Noah",
            "last_name": "King",
            "email": "noah.king@example.com",
            "status": "Active",
            "customer_type": "B2C",
        },
    ).json()
    customer_id = customer["customer_id"]

    client.post(
        f"/customers/{customer_id}/addresses",
        json={
            "address_type": "Shipping",
            "address_line1": "15 Harbor Road",
            "city": "Seattle",
            "state_province": "WA",
            "postal_code": "98101",
            "country_code": "US",
            "is_primary": True,
        },
    )
    client.post(
        f"/customers/{customer_id}/business-profiles",
        json={
            "company_name": "Blue Ocean LLC",
            "job_title": "Buyer",
            "lead_source": "Campaign",
            "lifecycle_stage": "Opportunity",
            "establishment_start_date": "2023-01-01",
            "onboarding_date": "2024-01-01",
        },
    )
    tag = client.post("/tags", json={"tag_name": "newsletter"}).json()
    client.post(f"/customers/{customer_id}/tags/{tag['tag_id']}")

    response = client.get(f"/customers/{customer_id}/details")

    assert response.status_code == 200
    body = response.json()
    assert body["customer_id"] == customer_id
    assert len(body["addresses"]) == 1
    assert body["tags"][0]["tag_name"] == "newsletter"


def test_create_customer_with_short_name_returns_422(client: TestClient) -> None:
    response = client.post(
        "/customers",
        json={
            "first_name": "A",
            "last_name": "B",
            "email": "short.name@example.com",
            "status": "Active",
            "customer_type": "B2C",
        },
    )

    assert response.status_code == 422


def test_create_business_profile_with_invalid_dates_returns_422(client: TestClient) -> None:
    customer = client.post(
        "/customers",
        json={
            "first_name": "Lara",
            "last_name": "Jones",
            "email": "lara.jones@example.com",
            "status": "Active",
            "customer_type": "B2B",
        },
    ).json()

    response = client.post(
        f"/customers/{customer['customer_id']}/business-profiles",
        json={
            "company_name": "Prime Co",
            "job_title": "Founder",
            "lead_source": "Web",
            "lifecycle_stage": "Lead",
            "establishment_start_date": "2025-06-01",
            "onboarding_date": "2025-01-01",
        },
    )

    assert response.status_code == 422
