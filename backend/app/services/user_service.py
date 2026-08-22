import random
import time
from collections.abc import Callable
from typing import TypeVar
from uuid import UUID

from psycopg import InterfaceError as PsycopgInterfaceError
from psycopg import OperationalError as PsycopgOperationalError
from sqlalchemy import select
from sqlalchemy.exc import DisconnectionError, IntegrityError, InterfaceError, OperationalError
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class DuplicateEmailError(Exception):
    pass


T = TypeVar("T")

READ_RETRY_MAX_ATTEMPTS = 3
READ_RETRY_INITIAL_DELAY_SECONDS = 0.05
READ_RETRY_MAX_DELAY_SECONDS = 0.125
READ_RETRY_MAX_JITTER_SECONDS = 0.025
TRANSIENT_DATABASE_ERRORS = (
    OperationalError,
    InterfaceError,
    DisconnectionError,
    PsycopgOperationalError,
    PsycopgInterfaceError,
)


def _retry_read_operation(db: Session, operation: Callable[[], T]) -> T:
    """Retry only idempotent reads; writes remain single-attempt to avoid duplicates."""
    for attempt in range(READ_RETRY_MAX_ATTEMPTS):
        try:
            return operation()
        except TRANSIENT_DATABASE_ERRORS:
            if attempt == READ_RETRY_MAX_ATTEMPTS - 1:
                raise

            db.invalidate()
            delay = min(
                READ_RETRY_INITIAL_DELAY_SECONDS * (2**attempt)
                + random.uniform(0, READ_RETRY_MAX_JITTER_SECONDS),
                READ_RETRY_MAX_DELAY_SECONDS,
            )
            time.sleep(delay)

    raise AssertionError("unreachable")


def create_user(db: Session, payload: UserCreate) -> User:
    user = User(**payload.model_dump())
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateEmailError from exc
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    return _retry_read_operation(
        db,
        lambda: list(db.scalars(select(User).order_by(User.created_at.desc()))),
    )


def get_user(db: Session, user_id: UUID) -> User | None:
    return _retry_read_operation(db, lambda: db.get(User, user_id))


def update_user(db: Session, user: User, payload: UserUpdate) -> User:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateEmailError from exc
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()
