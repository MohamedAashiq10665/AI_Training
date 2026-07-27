from app.core.security import hash_password
from app.repositories.user_repository import InMemoryUserRepository, UserRecord
from app.services.auth_service import AuthService

_user_repository = InMemoryUserRepository()
_user_repository.add_user(
    UserRecord(
        username="demo_user",
        password_hash=hash_password("ChangeMe123!"),
        is_active=True,
    )
)
_auth_service = AuthService(_user_repository)


def get_auth_service() -> AuthService:
    return _auth_service
