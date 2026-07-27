import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_auth_service
from app.core.security import hash_password
from app.main import app
from app.repositories.user_repository import InMemoryUserRepository, UserRecord
from app.services.auth_service import AuthService


@pytest.fixture
def service() -> AuthService:
    repository = InMemoryUserRepository()
    repository.add_user(
        UserRecord(
            username="alice",
            password_hash=hash_password("SecurePass123!"),
            is_active=True,
        )
    )
    repository.add_user(
        UserRecord(
            username="disabled_user",
            password_hash=hash_password("SecurePass123!"),
            is_active=False,
        )
    )
    return AuthService(repository)


@pytest.fixture
def client(service: AuthService) -> TestClient:
    app.dependency_overrides[get_auth_service] = lambda: service
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
