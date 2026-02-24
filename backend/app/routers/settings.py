import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.middleware.tenant import get_current_user, get_tenant_db
from app.middleware.tenant import SimpleUser as User
from app.models.settings import AppSettings
from app.schemas.settings import SettingsBase, SettingsResponse, SettingsUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["Settings"])


def _get_settings(db: Session) -> AppSettings:
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    if not settings:
        settings = AppSettings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("", response_model=SettingsResponse)
def get_settings(db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    return _get_settings(db)


@router.put("", response_model=SettingsResponse)
def update_settings(data: SettingsBase, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    settings = _get_settings(db)
    for key, value in data.model_dump().items():
        setattr(settings, key, value)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to update settings for user %s", current_user.id, exc_info=True)
        raise
    db.refresh(settings)
    return settings


@router.patch("", response_model=SettingsResponse)
def patch_settings(data: SettingsUpdate, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    settings = _get_settings(db)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(settings, key, value)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to patch settings for user %s", current_user.id, exc_info=True)
        raise
    db.refresh(settings)
    return settings
