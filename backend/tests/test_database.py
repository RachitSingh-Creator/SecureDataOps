import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/securedataops_test",
)

from app.db.database import engine


def test_database_connect_timeout(monkeypatch) -> None:
    connect_args: dict[str, object] = {}

    def connect(*args, **kwargs):
        connect_args.update(kwargs)
        return object()

    monkeypatch.setattr(engine.dialect, "connect", connect)

    engine.pool._creator()

    assert connect_args["connect_timeout"] == 10


def test_database_pool_configuration() -> None:
    assert engine.pool._pre_ping is True
    assert engine.pool.size() == 5
    assert engine.pool._max_overflow == 2
    assert engine.pool._timeout == 30
    assert engine.pool._recycle == 1800
