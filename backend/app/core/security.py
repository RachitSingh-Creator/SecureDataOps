from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from app.core.config import get_settings

bearer_scheme = HTTPBearer(auto_error=False)


def current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> UUID:
    """Validate an external bearer JWT and return its UUID subject claim."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()
    secret = settings.auth_jwt_secret.get_secret_value() if settings.auth_jwt_secret else None
    if not secret or len(secret) < 32 or not settings.auth_jwt_issuer or not settings.auth_jwt_audience:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication is not configured.")

    try:
        claims = jwt.decode(
            credentials.credentials,
            secret,
            algorithms=["HS256"],
            audience=settings.auth_jwt_audience or None,
            issuer=settings.auth_jwt_issuer or None,
            options={"require": ["exp", "sub"]},
        )
        return UUID(claims["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


def require_user_access(user_id: UUID, authenticated_user_id: UUID) -> None:
    if authenticated_user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this user record.")
