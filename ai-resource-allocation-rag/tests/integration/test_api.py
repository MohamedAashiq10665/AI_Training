import os

from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_api.db"

from backend.database.init_db import init_db
from backend.main import app

init_db(seed=True)
client = TestClient(app)


def test_health():
    response = client.get("/")
    assert response.status_code == 200


def _token(username: str, password: str) -> str:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_analytics_endpoint_with_auth():
    token = _token("viewer", "viewer123")
    response = client.get("/analytics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "total_employees" in response.json()


def test_rbac_viewer_cannot_access_bench():
    token = _token("viewer", "viewer123")
    response = client.get("/bench", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_manager_can_access_recommendation():
    token = _token("manager", "manager123")
    payload = {
        "project_name": "Healthcare API",
        "required_skills": ["Python", "Azure"],
        "preferred_certifications": ["Azure-AZ900"],
        "min_experience": 3,
        "required_count": 2,
    }
    response = client.post("/recommend", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "recommendations" in response.json()

