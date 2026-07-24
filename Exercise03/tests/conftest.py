import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_customer_service
from app.main import app
from app.repositories.mock_db import MockDatabase
from app.services.customer_service import CustomerService


class DummyActivityProvider:
    def get_customer_activity(self, external_user_id: int) -> dict:
        return {
            "open_todos": 2,
            "total_todos": 5,
            "recent_post_titles": [
                f"Update for user {external_user_id}",
                "Invoice follow-up",
                "Shipping note",
            ],
        }


class DummyWeatherProvider:
    def get_current_weather(self, city: str, country_code: str) -> dict:
        return {
            "provider": "openweathermap",
            "city": city,
            "temperature_c": 31.5,
            "condition": "Clear",
            "wind_speed_mps": 4.1,
        }


@pytest.fixture
def service() -> CustomerService:
    return CustomerService(MockDatabase(), DummyActivityProvider(), DummyWeatherProvider())


@pytest.fixture
def client(service: CustomerService) -> TestClient:
    app.dependency_overrides[get_customer_service] = lambda: service
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
