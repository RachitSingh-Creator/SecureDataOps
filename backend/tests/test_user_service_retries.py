import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/securedataops_test",
)

import pytest
from sqlalchemy.exc import OperationalError

from app.schemas.user import UserCreate
from app.services import user_service


class TransientReadDb:
    def __init__(self, failures_before_success: int) -> None:
        self.attempts = 0
        self.failures_before_success = failures_before_success
        self.invalidations = 0

    def scalars(self, _statement):
        self.attempts += 1
        if self.attempts <= self.failures_before_success:
            raise OperationalError("SELECT 1", {}, RuntimeError("connection interrupted"))
        return ["result"]

    def invalidate(self) -> None:
        self.invalidations += 1


def test_list_users_retries_transient_failures_with_bounded_backoff(monkeypatch) -> None:
    db = TransientReadDb(failures_before_success=2)
    delays: list[float] = []

    monkeypatch.setattr(user_service.random, "uniform", lambda _start, _end: 0.01)
    monkeypatch.setattr(user_service.time, "sleep", delays.append)

    assert user_service.list_users(db) == ["result"]
    assert db.attempts == 3
    assert db.invalidations == 2
    assert delays == pytest.approx([0.06, 0.11])
    assert all(delay <= user_service.READ_RETRY_MAX_DELAY_SECONDS for delay in delays)


def test_list_users_stops_after_the_retry_limit(monkeypatch) -> None:
    db = TransientReadDb(failures_before_success=3)
    delays: list[float] = []

    monkeypatch.setattr(user_service.random, "uniform", lambda _start, _end: 0)
    monkeypatch.setattr(user_service.time, "sleep", delays.append)

    with pytest.raises(OperationalError):
        user_service.list_users(db)

    assert db.attempts == user_service.READ_RETRY_MAX_ATTEMPTS
    assert db.invalidations == user_service.READ_RETRY_MAX_ATTEMPTS - 1
    assert delays == [0.05, 0.1]


def test_create_user_is_not_retried_after_a_database_failure() -> None:
    class WriteDb:
        def __init__(self) -> None:
            self.commits = 0

        def add(self, _user) -> None:
            pass

        def commit(self) -> None:
            self.commits += 1
            raise OperationalError("INSERT", {}, RuntimeError("connection interrupted"))

    db = WriteDb()

    with pytest.raises(OperationalError):
        user_service.create_user(db, UserCreate(name="Ada", email="ada@example.com"))

    assert db.commits == 1
