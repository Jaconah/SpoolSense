"""
Auth middleware for SpoolSense self-hosted.

Verifies a simple JWT (no metadata DB lookup) and opens the single spoolsense.db.
"""
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth import verify_token

security = HTTPBearer()


class SimpleUser:
    """Fixed single-owner user — no DB lookup needed."""
    id = 1
    tenant_id = "owner"


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> SimpleUser:
    """Verify JWT and return the fixed owner user."""
    token = credentials.credentials
    payload = verify_token(token, expected_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return SimpleUser()


def get_tenant_db(
    current_user: SimpleUser = Depends(get_current_user),
) -> Generator[Session, None, None]:
    """Yield the single spoolsense.db session."""
    yield from get_db()
