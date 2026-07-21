import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_customer_service
from app.main import app
from app.repositories.mock_db import MockDatabase
from app.services.customer_service import CustomerService


@pytest.fixture
def service() -> CustomerService:
    return CustomerService(MockDatabase())


@pytest.fixture
def client(service: CustomerService) -> TestClient:
    app.dependency_overrides[get_customer_service] = lambda: service
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
