from backend.utils.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hashing_and_verification():
    password = "my_secure_password"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)


def test_jwt_create_and_decode():
    token = create_access_token(subject="alice", role="manager", expires_minutes=30)
    payload = decode_access_token(token)
    assert payload["sub"] == "alice"
    assert payload["role"] == "manager"
