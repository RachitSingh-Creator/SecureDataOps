import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/securedataops_test")
os.environ.setdefault("AUTH_JWT_SECRET", "test-secret-that-is-never-used-outside-the-test-suite")
os.environ.setdefault("AUTH_JWT_ISSUER", "securedataops-test")
os.environ.setdefault("AUTH_JWT_AUDIENCE", "securedataops-api")

import logging

import jwt
import pytest
from fastapi import HTTPException, Response
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api import users
from app.core.audit import privacy_logger
from app.core.config import get_settings
from app.db.database import get_db
from app.main import app
from app.schemas.user import UserCreate, UserUpdate
from app.services import user_service


class FakeUser:
    def __init__(self, name: str, email: str, phone: str | None = None) -> None:
        self.id = uuid4()
        self.name = name
        self.email = email
        self.phone = phone
        self.created_at = datetime.now(UTC)
        self.updated_at = self.created_at


class FakeDb:
    def __init__(self) -> None:
        self.users: dict[UUID, FakeUser] = {}


@pytest.fixture()
def fake_db() -> FakeDb:
    return FakeDb()


@pytest.fixture(autouse=True)
def patch_user_service(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()

    def create_user(db: FakeDb, payload: UserCreate) -> FakeUser:
        if any(user.email == payload.email for user in db.users.values()):
            raise user_service.DuplicateEmailError
        user = FakeUser(**payload.model_dump())
        db.users[user.id] = user
        return user

    def list_users(db: FakeDb) -> list[FakeUser]:
        return list(db.users.values())

    def get_user(db: FakeDb, user_id: UUID) -> FakeUser | None:
        return db.users.get(user_id)

    def update_user(db: FakeDb, user: FakeUser, payload: UserUpdate) -> FakeUser:
        update_data = payload.model_dump(exclude_unset=True)
        if "email" in update_data and any(existing.email == update_data["email"] for existing in db.users.values() if existing.id != user.id):
            raise user_service.DuplicateEmailError
        for field, value in update_data.items():
            setattr(user, field, value)
        user.updated_at = datetime.now(UTC)
        return user

    def delete_user(db: FakeDb, user: FakeUser) -> None:
        db.users.pop(user.id)

    monkeypatch.setattr(user_service, "create_user", create_user)
    monkeypatch.setattr(user_service, "list_users", list_users)
    monkeypatch.setattr(user_service, "get_user", get_user)
    monkeypatch.setattr(user_service, "update_user", update_user)
    monkeypatch.setattr(user_service, "delete_user", delete_user)


def test_create_user_requires_valid_email() -> None:
    with pytest.raises(ValidationError):
        UserCreate(name="Ada Lovelace", email="not-an-email")


def test_user_crud_flow(fake_db: FakeDb) -> None:
    created = users.create_user(
        UserCreate(name="Ada Lovelace", email="ada@example.com", phone="+15551234567"),
        fake_db,
    )

    assert created.email == "ada@example.com"
    assert users.list_users(fake_db) == [created]
    assert users.get_user(created.id, created.id, fake_db).name == "Ada Lovelace"

    updated = users.update_user(created.id, UserUpdate(name="Ada Byron"), created.id, fake_db)
    assert updated.name == "Ada Byron"

    assert users.delete_user(created.id, created.id, fake_db) is None
    with pytest.raises(HTTPException) as exc_info:
        users.get_user(created.id, created.id, fake_db)
    assert exc_info.value.status_code == 404


def test_privacy_events_exclude_user_data_values(fake_db: FakeDb, caplog) -> None:
    privacy_logger.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.INFO, logger="securedataops.privacy"):
            created = users.create_user(
                UserCreate(name="Ada Lovelace", email="ada@example.com", phone="+15551234567"),
                fake_db,
            )
            users.get_user(created.id, created.id, fake_db)
            response = Response()
            users.export_user(created.id, response, created.id, fake_db)
            users.update_user(created.id, UserUpdate(name="Ada Byron"), created.id, fake_db)
            users.delete_user(created.id, created.id, fake_db)
    finally:
        privacy_logger.removeHandler(caplog.handler)

    events = [record.message for record in caplog.records if "privacy_action=" in record.message]
    assert {"user.created", "user.accessed", "user.exported", "user.corrected", "user.erased"} == {
        message.split()[0].split("=", 1)[1] for message in events
    }
    assert response.headers["content-disposition"] == f'attachment; filename="securedataops-user-{created.id}.json"'
    assert all(value not in " ".join(events) for value in ("Ada Lovelace", "Ada Byron", "ada@example.com", "+15551234567"))


def _authorization_header(user_id: UUID) -> dict[str, str]:
    token = jwt.encode(
        {
            "sub": str(user_id),
            "iss": "securedataops-test",
            "aud": "securedataops-api",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        os.environ["AUTH_JWT_SECRET"],
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    ("method", "path_suffix", "payload"),
    [
        ("get", "", None),
        ("get", "/export", None),
        ("put", "", {"name": "Updated"}),
        ("delete", "", None),
    ],
)
def test_privacy_endpoints_require_authentication(fake_db: FakeDb, method: str, path_suffix: str, payload: dict | None) -> None:
    user = users.create_user(UserCreate(name="Ada", email="ada@example.com"), fake_db)
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        response = TestClient(app).request(method.upper(), f"/api/v1/users/{user.id}{path_suffix}", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401


@pytest.mark.parametrize(
    ("method", "path_suffix", "payload"),
    [
        ("get", "", None),
        ("get", "/export", None),
        ("put", "", {"name": "Updated"}),
        ("delete", "", None),
    ],
)
def test_privacy_endpoints_reject_cross_user_access(
    fake_db: FakeDb,
    method: str,
    path_suffix: str,
    payload: dict | None,
) -> None:
    owner = users.create_user(UserCreate(name="Ada", email="ada@example.com"), fake_db)
    other = users.create_user(UserCreate(name="Grace", email="grace@example.com"), fake_db)
    app.dependency_overrides[get_db] = lambda: fake_db
    try:
        client = TestClient(app)
        response = client.request(
            method.upper(),
            f"/api/v1/users/{owner.id}{path_suffix}",
            headers=_authorization_header(other.id),
            json=payload,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
