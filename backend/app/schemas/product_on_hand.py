"""Pydantic schemas for Product on Hand endpoints."""
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import List


class ProductOnHandCreate(BaseModel):
    """Schema for creating a new Product on Hand."""
    project_id: int | None = None
    print_job_id: int
    name: str = Field(..., min_length=1, max_length=200)
    status: str = Field(default="completed", pattern=r"^(printed|completed)$")
    location: str | None = Field(None, min_length=1, max_length=200)
    notes: str | None = None


class ProductOnHandUpdate(BaseModel):
    """Schema for updating a Product on Hand."""
    name: str | None = Field(None, min_length=1, max_length=200)
    status: str | None = Field(None, pattern=r"^(printed|completed)$")
    location: str | None = Field(None, min_length=1, max_length=200)
    notes: str | None = None


class HardwareItemDetail(BaseModel):
    """Hardware item detail for Product on Hand."""
    id: int
    name: str
    quantity: int
    cost_per_item: float


class ProductOnHandResponse(BaseModel):
    """Schema for Product on Hand API responses with computed fields."""
    id: int
    project_id: int | None
    print_job_id: int
    name: str
    status: str
    location: str | None
    notes: str | None
    created_at: datetime

    # Computed fields
    project_name: str | None
    color: str
    filament_cost: float
    hardware_cost: float
    total_cost: float
    sell_price: float | None
    potential_profit: float | None
    hardware_items: List[HardwareItemDetail]

    model_config = ConfigDict(from_attributes=True)


class ConvertToOrderRequest(BaseModel):
    """Schema for converting a Product on Hand to an Order."""
    customer_name: str | None = Field(None, max_length=200)
    customer_contact: str | None = Field(None, max_length=200)
    customer_location: str | None = Field(None, max_length=200)
    quoted_price: float | None = Field(None, ge=0)
    notes: str | None = Field(None, max_length=2000)


class ProductOnHandStats(BaseModel):
    """Schema for Product on Hand statistics."""
    total_count: int
    total_value: float  # Sum of sell_price
    total_potential_profit: float
