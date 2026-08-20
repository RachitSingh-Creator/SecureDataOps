import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/securedataops_test")

from app.main import health


def test_health_endpoint() -> None:
    assert health() == {"status": "healthy"}
