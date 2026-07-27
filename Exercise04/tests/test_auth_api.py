from jose import jwt

from app.core.security import ALGORITHM, SECRET_KEY


def test_login_success_returns_jwt(client):
    response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "SecurePass123!"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]

    payload = jwt.decode(body["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "alice"


def test_login_wrong_password_returns_unauthorized(client):
    response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "WrongPassword123!"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_login_unknown_user_returns_unauthorized(client):
    response = client.post(
        "/auth/login",
        json={"username": "unknown", "password": "AnyPassword123!"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_login_rejects_empty_fields(client):
    response = client.post(
        "/auth/login",
        json={"username": "", "password": ""},
    )

    assert response.status_code == 422


def test_login_rejects_invalid_username_format(client):
    response = client.post(
        "/auth/login",
        json={"username": "bad user", "password": "SecurePass123!"},
    )

    assert response.status_code == 422


def test_login_rejects_short_password(client):
    response = client.post(
        "/auth/login",
        json={"username": "alice", "password": "short"},
    )

    assert response.status_code == 422


def test_login_inactive_user_forbidden(client):
    response = client.post(
        "/auth/login",
        json={"username": "disabled_user", "password": "SecurePass123!"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Inactive account"
