import os
from collections.abc import Generator
from datetime import UTC, datetime
from uuid import UUID, uuid4

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/securedataops_test")

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.api import users
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
    assert users.get_user(created.id, fake_db).name == "Ada Lovelace"

    updated = users.update_user(created.id, UserUpdate(name="Ada Byron"), fake_db)
    assert updated.name == "Ada Byron"

    assert users.delete_user(created.id, fake_db) is None
    with pytest.raises(HTTPException) as exc_info:
        users.get_user(created.id, fake_db)
    assert exc_info.value.status_code == 404
