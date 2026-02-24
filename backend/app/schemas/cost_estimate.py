from pydantic import BaseModel, Field


class CostEstimateRequest(BaseModel):
    spool_id: int
    grams: float = Field(..., gt=0)
    print_time_minutes: int = Field(..., gt=0)


class QuickEstimateRequest(BaseModel):
    cost_per_kg: float = Field(..., ge=0)
    grams: float = Field(..., gt=0)
    print_time_minutes: int = Field(..., gt=0)


class CostBreakdown(BaseModel):
    filament_cost: float
    electricity_cost: float
    time_cost: float
    depreciation_cost: float
    fixed_fee: float
    subtotal: float
    profit_margin_percent: float
    profit: float
    total: float
    currency_symbol: str


class CustomerQuote(BaseModel):
    total: float
    currency_symbol: str
