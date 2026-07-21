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
    assert body["customer_id"] == 3
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
    response = client.post("/customers/1/tags/1")

    assert response.status_code == 409
    assert response.json()["detail"] == "Tag 1 is already assigned to customer 1."


def test_get_customer_details_returns_nested_data(client: TestClient) -> None:
    response = client.get("/customers/1/details")

    assert response.status_code == 200
    body = response.json()
    assert body["customer_id"] == 1
    assert len(body["addresses"]) == 1
    assert body["tags"][0]["tag_name"] == "vip"
