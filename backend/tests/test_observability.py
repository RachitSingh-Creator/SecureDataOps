import logging
import os
from uuid import UUID, uuid4

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/securedataops_test",
)

from fastapi.testclient import TestClient

from app.main import REQUEST_ID_HEADER, app, logger


def test_request_id_is_generated_and_returned() -> None:
    response = TestClient(app).get("/health")

    assert UUID(response.headers[REQUEST_ID_HEADER])


def test_request_id_is_preserved_and_returned() -> None:
    request_id = str(uuid4())

    response = TestClient(app).get("/health", headers={REQUEST_ID_HEADER: request_id})

    assert response.headers[REQUEST_ID_HEADER] == request_id


def test_request_is_logged(caplog) -> None:
    logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.INFO, logger="securedataops"):
            response = TestClient(app).get("/health")
    finally:
        logger.removeHandler(caplog.handler)

    assert response.status_code == 200
    request_id = response.headers[REQUEST_ID_HEADER]
    assert any(
        f"request request_id={request_id} method=GET path=/health status_code=200 duration_ms="
        in record.message
        for record in caplog.records
    )


def test_unexpected_error_is_generic_and_keeps_security_headers(caplog) -> None:
    async def unexpected_error():
        raise RuntimeError("DATABASE_URL=postgresql://user:password@host/db")

    logger.addHandler(caplog.handler)
    try:
        app.add_api_route("/_test-unexpected-error", unexpected_error)
        response = TestClient(app, raise_server_exceptions=False).get("/_test-unexpected-error")
    finally:
        logger.removeHandler(caplog.handler)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    assert "DATABASE_URL" not in response.text
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers[REQUEST_ID_HEADER]
    assert all("DATABASE_URL" not in record.message for record in caplog.records)
