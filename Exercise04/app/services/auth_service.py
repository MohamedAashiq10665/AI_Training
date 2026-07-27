from app.core.security import create_access_token, hash_password, verify_password
from app.repositories.user_repository import InMemoryUserRepository, UserRecord


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 401) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthService:
    def __init__(self, user_repository: InMemoryUserRepository) -> None:
        self._user_repository = user_repository

    def register_user(self, username: str, password: str) -> dict:
        existing = self._user_repository.get_by_username(username)
        if existing:
            raise AuthError("Username already exists", status_code=409)

        user = UserRecord(username=username, password_hash=hash_password(password), is_active=True)
        self._user_repository.add_user(user)
        return {"username": user.username, "is_active": user.is_active}

    def authenticate_user(self, username: str, password: str) -> str:
        user = self._user_repository.get_by_username(username)
        if not user:
            raise AuthError("Invalid username or password", status_code=401)

        if not user.is_active:
            raise AuthError("Inactive account", status_code=403)

        if not verify_password(password, user.password_hash):
            raise AuthError("Invalid username or password", status_code=401)

        return create_access_token(subject=user.username)
