"""
Authentication router for SpoolSense self-hosted.

Single-user, password-only auth. No email, no device verification, no TOTP.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.tenant import get_current_user, SimpleUser, security
from app.models.settings import AppSettings
from app.services import auth as auth_service
from app.config import settings
from app.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================================
# Password Validation
# ============================================================================

def validate_password_complexity(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    return password


# ============================================================================
# Schemas
# ============================================================================

class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        return validate_password_complexity(v)


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=100)


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
def login(
    login_request: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Authenticate with password and receive a JWT access token."""
    app_settings = db.query(AppSettings).filter_by(id=1).first()
    if not app_settings or not app_settings.password_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="App not configured — password not set",
        )

    if not auth_service.verify_password(login_request.password, app_settings.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )

    access_token = auth_service.create_access_token()
    refresh_token = auth_service.create_refresh_token_jwt()
    _set_refresh_cookie(response, refresh_token)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"id": 1, "name": "Owner", "tenant_id": "owner"},
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    """Clear the refresh token cookie."""
    _clear_refresh_cookie(response)
    return None


@router.post("/refresh", response_model=RefreshResponse)
@limiter.limit("30/hour")
def refresh_token(request: Request):
    """Exchange refresh token cookie for a new access token."""
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    payload = auth_service.verify_token(refresh_token_value, expected_type="refresh")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token = auth_service.create_access_token()
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
def get_current_user_info(current_user: SimpleUser = Depends(get_current_user)):
    """Return fixed owner user info."""
    return {"id": 1, "name": "Owner", "tenant_id": "owner"}


@router.post("/change-password", status_code=200)
def change_password(
    request: ChangePasswordRequest,
    current_user: SimpleUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the owner password stored in AppSettings."""
    app_settings = db.query(AppSettings).filter_by(id=1).first()
    if not app_settings:
        raise HTTPException(status_code=500, detail="Settings not found")

    if not auth_service.verify_password(request.current_password, app_settings.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    app_settings.password_hash = auth_service.hash_password(request.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@router.patch("/profile", status_code=200)
def update_profile(
    request: ProfileUpdateRequest,
    current_user: SimpleUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update display name (stored in AppSettings.owner_name)."""
    # Self-hosted has no user table; profile update is a no-op / future extension
    return {"id": 1, "name": request.name or "Owner", "tenant_id": "owner"}


# ============================================================================
# Cookie Helpers
# ============================================================================

def _set_refresh_cookie(response: Response, token: str) -> None:
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        "refresh_token",
        token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="strict",
        max_age=max_age,
        path="/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie("refresh_token", path="/auth")
