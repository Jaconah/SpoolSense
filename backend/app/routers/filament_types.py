import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.middleware.tenant import get_current_user, get_tenant_db
from app.middleware.tenant import SimpleUser as User
from app.models.filament import FilamentType
from app.schemas.filament import (
    FilamentTypeCreate,
    FilamentTypeResponse,
    FilamentTypeUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/filament-types", tags=["Filament Types"])


@router.get("", response_model=list[FilamentTypeResponse])
def list_filament_types(db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(FilamentType)
        .order_by(FilamentType.usage_count.desc(), FilamentType.name.asc())
        .all()
    )


@router.post("", response_model=FilamentTypeResponse, status_code=201)
def create_filament_type(data: FilamentTypeCreate, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    existing = db.query(FilamentType).filter(
        func.lower(FilamentType.name) == data.name.lower()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Filament type already exists")
    ft = FilamentType(**data.model_dump())
    db.add(ft)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to create filament type for user %s", current_user.id, exc_info=True)
        raise
    db.refresh(ft)
    return ft


@router.get("/{ft_id}", response_model=FilamentTypeResponse)
def get_filament_type(ft_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    ft = db.query(FilamentType).filter(FilamentType.id == ft_id).first()
    if not ft:
        raise HTTPException(status_code=404, detail="Filament type not found")
    return ft


@router.put("/{ft_id}", response_model=FilamentTypeResponse)
def update_filament_type(
    ft_id: int, data: FilamentTypeUpdate, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)
):
    ft = db.query(FilamentType).filter(FilamentType.id == ft_id).first()
    if not ft:
        raise HTTPException(status_code=404, detail="Filament type not found")
    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing = db.query(FilamentType).filter(
            func.lower(FilamentType.name) == update_data["name"].lower(),
            FilamentType.id != ft_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Filament type already exists")
    for key, value in update_data.items():
        setattr(ft, key, value)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to update filament type %s for user %s", ft_id, current_user.id, exc_info=True)
        raise
    db.refresh(ft)
    return ft


@router.delete("/{ft_id}", status_code=204)
def delete_filament_type(ft_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    ft = db.query(FilamentType).filter(FilamentType.id == ft_id).first()
    if not ft:
        raise HTTPException(status_code=404, detail="Filament type not found")
    if ft.spools:
        raise HTTPException(
            status_code=400, detail="Cannot delete: filament type has associated spools"
        )
    db.delete(ft)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to delete filament type %s for user %s", ft_id, current_user.id, exc_info=True)
        raise
