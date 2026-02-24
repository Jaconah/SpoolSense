import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.middleware.tenant import get_current_user, get_tenant_db
from app.middleware.tenant import SimpleUser as User
from app.models.filament import Manufacturer
from app.schemas.filament import (
    ManufacturerCreate,
    ManufacturerResponse,
    ManufacturerUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/manufacturers", tags=["Manufacturers"])


@router.get("", response_model=list[ManufacturerResponse])
def list_manufacturers(db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Manufacturer)
        .order_by(Manufacturer.usage_count.desc(), Manufacturer.name.asc())
        .all()
    )


@router.post("", response_model=ManufacturerResponse, status_code=201)
def create_manufacturer(data: ManufacturerCreate, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    existing = db.query(Manufacturer).filter(
        func.lower(Manufacturer.name) == data.name.lower()
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Manufacturer already exists")
    mfg = Manufacturer(**data.model_dump())
    db.add(mfg)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to create manufacturer for user %s", current_user.id, exc_info=True)
        raise
    db.refresh(mfg)
    return mfg


@router.get("/{mfg_id}", response_model=ManufacturerResponse)
def get_manufacturer(mfg_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    mfg = db.query(Manufacturer).filter(Manufacturer.id == mfg_id).first()
    if not mfg:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    return mfg


@router.put("/{mfg_id}", response_model=ManufacturerResponse)
def update_manufacturer(
    mfg_id: int, data: ManufacturerUpdate, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)
):
    mfg = db.query(Manufacturer).filter(Manufacturer.id == mfg_id).first()
    if not mfg:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing = db.query(Manufacturer).filter(
            func.lower(Manufacturer.name) == update_data["name"].lower(),
            Manufacturer.id != mfg_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Manufacturer already exists")
    for key, value in update_data.items():
        setattr(mfg, key, value)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to update manufacturer %s for user %s", mfg_id, current_user.id, exc_info=True)
        raise
    db.refresh(mfg)
    return mfg


@router.delete("/{mfg_id}", status_code=204)
def delete_manufacturer(mfg_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    mfg = db.query(Manufacturer).filter(Manufacturer.id == mfg_id).first()
    if not mfg:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    if mfg.spools:
        raise HTTPException(
            status_code=400, detail="Cannot delete: manufacturer has associated spools"
        )
    db.delete(mfg)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to delete manufacturer %s for user %s", mfg_id, current_user.id, exc_info=True)
        raise
