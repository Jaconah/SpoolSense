from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.hardware import HardwareItemResponse


class OrderHardwareResponse(BaseModel):
    id: int
    hardware_item_id: int | None
    quantity: int
    unit_cost_snapshot: float
    hardware_name_snapshot: str | None = None
    hardware_brand_snapshot: str | None = None
    is_one_off: bool = False
    one_off_name: str | None = None
    one_off_cost: float | None = None
    hardware_item: Optional[HardwareItemResponse] = None

    model_config = {"from_attributes": True}


class OrderSpoolInput(BaseModel):
    """Input schema for a single spool entry in a multi-color order."""
    spool_id: int = Field(..., gt=0)
    filament_grams: float = Field(..., gt=0)
    position: int = Field(..., ge=1, le=6)


class OrderSpoolResponse(BaseModel):
    """Response schema for a single spool entry in a multi-color order."""
    id: int
    spool_id: int
    filament_grams: float
    position: int
    cost_per_kg_snapshot: float

    model_config = {"from_attributes": True}


class OrderBase(BaseModel):
    project_id: int | None = None
    spool_id: int | None = None
    custom_name: str | None = Field(None, max_length=200)
    custom_price: float | None = None
    customer_name: str | None = Field(None, max_length=100)
    customer_contact: str | None = Field(None, max_length=200)
    customer_location: str | None = Field(None, max_length=200)
    status: str = Field(default="ordered", pattern=r"^(ordered|printed|finished|sold)$")
    quoted_price: float | None = Field(None, ge=0)
    due_date: datetime | None = None
    shipping_charge: float | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=1000)


class OrderHardwareInput(BaseModel):
    hardware_item_id: int | None = None
    quantity: int = Field(default=1, ge=1)
    is_one_off: bool = False
    one_off_name: str | None = None
    one_off_cost: float | None = Field(None, ge=0)

    @model_validator(mode='after')
    def validate_item_type(self) -> 'OrderHardwareInput':
        if self.is_one_off:
            if not self.one_off_name:
                raise ValueError("one_off_name is required for one-off items")
            if self.one_off_cost is None:
                raise ValueError("one_off_cost is required for one-off items")
        else:
            if self.hardware_item_id is None:
                raise ValueError("hardware_item_id is required for inventory items")
        return self


class OrderCreate(OrderBase):
    hardware_items: list[OrderHardwareInput] = Field(default_factory=list)
    spools: list[OrderSpoolInput] = Field(default_factory=list)  # Multi-color spools


class OrderUpdate(BaseModel):
    project_id: int | None = None
    spool_id: int | None = None
    custom_name: str | None = Field(None, max_length=200)
    custom_price: float | None = None
    customer_name: str | None = Field(None, max_length=100)
    customer_contact: str | None = Field(None, max_length=200)
    customer_location: str | None = Field(None, max_length=200)
    status: str | None = Field(None, pattern=r"^(ordered|printed|finished|sold)$")
    quoted_price: float | None = Field(None, ge=0)
    due_date: datetime | None = None
    shipping_charge: float | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=1000)
    hardware_items: list[OrderHardwareInput] | None = None  # If provided, replaces all hardware
    spools: list[OrderSpoolInput] | None = None  # If provided, replaces all order spools


class OrderResponse(OrderBase):
    id: int
    order_hardware: list[OrderHardwareResponse]
    order_spools: list[OrderSpoolResponse] = Field(default_factory=list)
    filament_grams_snapshot: float | None = None
    print_time_hours_snapshot: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderProfitBreakdown(BaseModel):
    revenue: float
    shipping_revenue: float
    filament_cost: float
    hardware_cost: float
    electricity_cost: float
    time_cost: float
    depreciation_cost: float
    total_cost: float
    profit: float
    currency_symbol: str


class OrderSummary(BaseModel):
    total_orders: int
    ordered_orders: int
    printed_orders: int
    finished_orders: int
    sold_orders: int
    total_revenue: float
    total_cost: float
    total_profit: float
    currency_symbol: str


# --- Order Invoice (Issue #100) ---

class OrderInvoiceFilamentLine(BaseModel):
    color_name: str
    filament_type: str
    color_hex: str
    grams: float


class OrderInvoiceHardwareLine(BaseModel):
    name: str
    brand: str | None
    quantity: int
    unit_cost: float


class OrderInvoiceResponse(BaseModel):
    order_id: int
    customer_name: str | None
    customer_contact: str | None
    customer_location: str | None
    status: str
    item_name: str | None
    quoted_price: float | None
    shipping_charge: float | None
    due_date: datetime | None
    created_at: datetime
    filament_lines: list[OrderInvoiceFilamentLine]
    hardware_lines: list[OrderInvoiceHardwareLine]
    currency_symbol: str
    notes: str | None
