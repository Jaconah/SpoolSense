import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.middleware.tenant import get_current_user, get_tenant_db
from app.middleware.tenant import SimpleUser as User
from app.models.hardware import HardwareItem
from app.models.settings import AppSettings
from app.schemas.common import PaginatedResponse
from app.schemas.hardware import (
    HardwareItemCreate,
    HardwareItemResponse,
    HardwareItemUpdate,
    HardwareSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hardware", tags=["Hardware"])


@router.get("/summary", response_model=HardwareSummary)
def get_hardware_summary(db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    currency = settings.currency_symbol if settings else "$"

    total_items = db.query(func.count(HardwareItem.id)).scalar() or 0

    # Total invested
    total_invested = (
        db.query(func.coalesce(func.sum(HardwareItem.purchase_price), 0.0)).scalar()
    )

    # Current stock value
    all_items = db.query(HardwareItem).all()
    total_in_stock_value = sum(
        item.cost_per_item * item.quantity_in_stock for item in all_items
    )

    # Low stock items
    low_stock_items = sum(1 for item in all_items if item.is_low_stock)

    return HardwareSummary(
        total_items=total_items,
        total_invested=round(total_invested, 2),
        total_in_stock_value=round(total_in_stock_value, 2),
        low_stock_items=low_stock_items,
        currency_symbol=currency,
    )


@router.get("", response_model=PaginatedResponse[HardwareItemResponse])
def list_hardware(
    low_stock_only: bool = Query(False),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user),
):
    query = db.query(HardwareItem)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(
            HardwareItem.name.ilike(term),
            HardwareItem.brand.ilike(term),
            HardwareItem.notes.ilike(term),
        ))
    if low_stock_only:
        query = query.filter(
            HardwareItem.low_stock_threshold.isnot(None),
            HardwareItem.quantity_in_stock <= HardwareItem.low_stock_threshold,
        )
    total = query.count()
    items = (
        query
        .order_by(HardwareItem.name)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.post("", response_model=HardwareItemResponse, status_code=201)
def create_hardware(data: HardwareItemCreate, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    item_data = data.model_dump()
    # If quantity_in_stock not provided, initialize to quantity_purchased
    if "quantity_in_stock" not in item_data or item_data["quantity_in_stock"] == 0:
        item_data["quantity_in_stock"] = item_data.get("quantity_purchased", 1)
    item = HardwareItem(**item_data)
    db.add(item)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to create hardware item for user %s", current_user.id, exc_info=True)
        raise
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=HardwareItemResponse)
def get_hardware(item_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    item = db.query(HardwareItem).filter(HardwareItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Hardware item not found")
    return item


@router.put("/{item_id}", response_model=HardwareItemResponse)
def update_hardware(item_id: int, data: HardwareItemUpdate, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    item = db.query(HardwareItem).filter(HardwareItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Hardware item not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(item, key, value)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to update hardware item %s for user %s", item_id, current_user.id, exc_info=True)
        raise
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
def delete_hardware(item_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    item = db.query(HardwareItem).filter(HardwareItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Hardware item not found")
    db.delete(item)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to delete hardware item %s for user %s", item_id, current_user.id, exc_info=True)
        raise
