from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.middleware.tenant import get_current_user, get_tenant_db
from app.middleware.tenant import SimpleUser as User
from app.models.filament import Spool
from app.models.settings import AppSettings
from app.schemas.cost_estimate import (
    CostBreakdown,
    CostEstimateRequest,
    CustomerQuote,
    QuickEstimateRequest,
)
from app.services.cost_calculator import calculate_cost

router = APIRouter(tags=["Cost Estimator"])


def _get_settings(db: Session) -> AppSettings:
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    if not settings:
        raise HTTPException(status_code=500, detail="Settings not initialized")
    return settings


@router.post("/cost-estimate", response_model=CostBreakdown)
def estimate_cost(data: CostEstimateRequest, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    spool = db.query(Spool).filter(Spool.id == data.spool_id).first()
    if not spool:
        raise HTTPException(status_code=404, detail="Spool not found")
    settings = _get_settings(db)
    return calculate_cost(
        grams=data.grams,
        print_time_minutes=data.print_time_minutes,
        cost_per_kg=spool.cost_per_kg,
        settings=settings,
    )


@router.post("/cost-estimate/quick", response_model=CostBreakdown)
def quick_estimate(data: QuickEstimateRequest, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    settings = _get_settings(db)
    return calculate_cost(
        grams=data.grams,
        print_time_minutes=data.print_time_minutes,
        cost_per_kg=data.cost_per_kg,
        settings=settings,
    )
