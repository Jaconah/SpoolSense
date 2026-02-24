from pydantic import BaseModel

from app.schemas.filament import SpoolResponse


class DashboardStats(BaseModel):
    total_spools: int
    total_orders: int
    sold_orders: int
    order_revenue: float
    currency_symbol: str


class DashboardResponse(BaseModel):
    stats: DashboardStats
    spools: list[SpoolResponse]
