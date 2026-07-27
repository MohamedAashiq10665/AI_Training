from dataclasses import dataclass
from threading import Lock


@dataclass
class UserRecord:
    username: str
    password_hash: str
    is_active: bool = True


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._users: dict[str, UserRecord] = {}

    def add_user(self, user: UserRecord) -> None:
        with self._lock:
            if user.username in self._users:
                raise ValueError("Username already exists")
            self._users[user.username] = user

    def get_by_username(self, username: str) -> UserRecord | None:
        with self._lock:
            return self._users.get(username)
