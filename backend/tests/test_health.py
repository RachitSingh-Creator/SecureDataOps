import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/securedataops_test",
)

from fastapi.testclient import TestClient

from app.main import app, health


def test_health_endpoint() -> None:
    assert health() == {"status": "healthy"}


def test_security_headers() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"