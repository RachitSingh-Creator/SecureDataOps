import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/securedataops_test",
)

import pytest
from fastapi.testclient import TestClient
from psycopg import OperationalError as PsycopgOperationalError
from sqlalchemy.exc import OperationalError as SQLAlchemyOperationalError

from app.main import REQUEST_ID_HEADER, app
from app.services import user_service


@pytest.mark.parametrize(
    "database_error",
    [
        SQLAlchemyOperationalError(
            "SELECT 1",
            {},
            RuntimeError("connection to db.internal failed for postgresql://user:password@host/db"),
        ),
        PsycopgOperationalError("connection to db.internal failed"),
    ],
)
def test_database_operational_errors_return_generic_503(monkeypatch, database_error) -> None:
    def database_unavailable(_db):
        raise database_error

    monkeypatch.setattr(user_service, "list_users", database_unavailable)

    response = TestClient(app, raise_server_exceptions=False).get("/api/v1/users")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database temporarily unavailable."}
    assert response.headers[REQUEST_ID_HEADER]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "postgresql://" not in response.text
    assert "db.internal" not in response.text
