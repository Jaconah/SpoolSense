from datetime import datetime

from pydantic import BaseModel, Field


class HardwareItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    brand: str | None = Field(None, max_length=100)
    purchase_url: str | None = Field(None, max_length=500)
    purchase_price: float = Field(default=0.0, ge=0)
    quantity_purchased: int = Field(default=1, ge=1)
    quantity_in_stock: int = Field(default=0, ge=0)
    low_stock_threshold: int | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=1000)


class HardwareItemCreate(HardwareItemBase):
    pass


class HardwareItemUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    brand: str | None = Field(None, max_length=100)
    purchase_url: str | None = Field(None, max_length=500)
    purchase_price: float | None = Field(None, ge=0)
    quantity_purchased: int | None = Field(None, ge=1)
    quantity_in_stock: int | None = Field(None, ge=0)
    low_stock_threshold: int | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=1000)


class HardwareItemResponse(HardwareItemBase):
    id: int
    cost_per_item: float
    is_low_stock: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HardwareSummary(BaseModel):
    total_items: int
    total_invested: float
    total_in_stock_value: float
    low_stock_items: int
    currency_symbol: str
