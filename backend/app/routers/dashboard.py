from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.middleware.tenant import get_current_user, get_tenant_db
from app.middleware.tenant import SimpleUser as User
from app.models.filament import Spool
from app.models.order import Order
from app.models.settings import AppSettings
from app.schemas.dashboard import DashboardResponse, DashboardStats

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    currency = settings.currency_symbol if settings else "$"

    total_spools = db.query(func.count(Spool.id)).scalar() or 0

    total_orders = db.query(func.count(Order.id)).scalar() or 0
    sold_orders = (
        db.query(func.count(Order.id)).filter(Order.status == "sold").scalar() or 0
    )
    order_revenue = (
        db.query(func.coalesce(func.sum(Order.quoted_price), 0.0))
        .filter(Order.status == "sold", Order.quoted_price.isnot(None))
        .scalar()
    )

    stats = DashboardStats(
        total_spools=total_spools,
        total_orders=total_orders,
        sold_orders=sold_orders,
        order_revenue=round(order_revenue, 2),
        currency_symbol=currency,
    )

    spool_list = (
        db.query(Spool)
        .options(joinedload(Spool.filament_type), joinedload(Spool.manufacturer))
        .order_by(Spool.remaining_weight_g.asc())
        .all()
    )

    return DashboardResponse(
        stats=stats,
        spools=spool_list,
    )
