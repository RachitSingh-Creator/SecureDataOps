from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.audit import log_privacy_event
from app.core.security import current_user_id, require_user_access
from app.db.database import get_db
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user_service
from app.services.user_service import DuplicateEmailError

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        user = user_service.create_user(db, payload)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.") from exc
    log_privacy_event("user.created", user.id)
    return user


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    users = user_service.list_users(db)
    log_privacy_event("user.list_accessed")
    return users


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, authenticated_user_id: UUID = Depends(current_user_id), db: Session = Depends(get_db)):
    require_user_access(user_id, authenticated_user_id)
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    log_privacy_event("user.accessed", user.id)
    return user


@router.get("/{user_id}/export", response_model=UserRead)
def export_user(
    user_id: UUID,
    response: Response,
    authenticated_user_id: UUID = Depends(current_user_id),
    db: Session = Depends(get_db),
):
    require_user_access(user_id, authenticated_user_id)
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    response.headers["Content-Disposition"] = f'attachment; filename="securedataops-user-{user.id}.json"'
    log_privacy_event("user.exported", user.id)
    return user


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    authenticated_user_id: UUID = Depends(current_user_id),
    db: Session = Depends(get_db),
):
    require_user_access(user_id, authenticated_user_id)
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    try:
        updated_user = user_service.update_user(db, user, payload)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists.") from exc
    log_privacy_event("user.corrected", updated_user.id)
    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    authenticated_user_id: UUID = Depends(current_user_id),
    db: Session = Depends(get_db),
):
    require_user_access(user_id, authenticated_user_id)
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    user_service.delete_user(db, user)
    log_privacy_event("user.erased", user.id)
