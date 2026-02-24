from datetime import datetime

from pydantic import BaseModel, Field


# --- Filament Types ---

class FilamentTypeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    abbreviation: str = Field(..., min_length=1, max_length=10)
    description: str | None = Field(None, max_length=500)


class FilamentTypeCreate(FilamentTypeBase):
    pass


class FilamentTypeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    abbreviation: str | None = Field(None, min_length=1, max_length=10)
    description: str | None = Field(None, max_length=500)


class FilamentTypeResponse(FilamentTypeBase):
    id: int
    is_default: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Manufacturers ---

class ManufacturerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    website: str | None = Field(None, max_length=500)


class ManufacturerCreate(ManufacturerBase):
    pass


class ManufacturerUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    website: str | None = Field(None, max_length=500)


class ManufacturerResponse(ManufacturerBase):
    id: int
    is_default: bool
    usage_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Spools ---

class SpoolBase(BaseModel):
    filament_type_id: int
    manufacturer_id: int
    color_name: str = Field(..., min_length=1, max_length=100)
    color_hex: str = Field(default="#000000", pattern=r"^#[0-9a-fA-F]{6}$")
    total_weight_g: float = Field(default=1000.0, gt=0)
    remaining_weight_g: float = Field(default=1000.0, ge=0)
    cost_per_kg: float = Field(default=0.0, ge=0)

    # New pricing schema
    msrp: float = Field(default=0.0, ge=0)  # Customer pricing reference
    purchase_price: float = Field(default=0.0, ge=0)  # What you paid (P&L)

    # Legacy pricing fields (kept for backwards compatibility)
    normal_price: float | None = None
    is_sale_price: bool = False

    purchase_date: datetime | None = None
    tracking_id: str | None = Field(None, max_length=50)
    location: str | None = Field(None, max_length=200)
    notes: str | None = Field(None, max_length=1000)
    is_active: bool = True


class SpoolCreate(SpoolBase):
    pass


class SpoolUpdate(BaseModel):
    filament_type_id: int | None = None
    manufacturer_id: int | None = None
    color_name: str | None = Field(None, min_length=1, max_length=100)
    color_hex: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    total_weight_g: float | None = Field(None, gt=0)
    remaining_weight_g: float | None = Field(None, ge=0)
    cost_per_kg: float | None = Field(None, ge=0)

    # New pricing schema
    msrp: float | None = Field(None, ge=0)
    purchase_price: float | None = Field(None, ge=0)

    # Legacy pricing fields (kept for backwards compatibility)
    normal_price: float | None = None
    is_sale_price: bool | None = None

    purchase_date: datetime | None = None
    tracking_id: str | None = Field(None, max_length=50)
    location: str | None = Field(None, max_length=200)
    notes: str | None = Field(None, max_length=1000)
    is_active: bool | None = None


class SpoolAdjust(BaseModel):
    remaining_weight_g: float = Field(..., ge=0)


class SpoolResponse(SpoolBase):
    id: int
    remaining_percent: float
    # Override to allow negative values when spool negative prevention is disabled
    remaining_weight_g: float
    filament_type: FilamentTypeResponse
    manufacturer: ManufacturerResponse
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Spool Validation (Issue #17) ---

class SpoolShortageResponse(BaseModel):
    """Details about a spool that would go negative."""
    spool_id: int
    tracking_id: str | None
    color_name: str
    filament_type_name: str
    manufacturer_name: str | None
    current_weight_g: float
    requested_weight_g: float
    resulting_weight_g: float
    shortage_g: float
    within_reserve: bool = False  # True = has enough but dips into safety buffer


class SpoolValidationResponse(BaseModel):
    """Result of spool inventory validation."""
    is_valid: bool
    has_warnings: bool
    shortages: list[SpoolShortageResponse]
    message: str | None = None


# --- Spool Usage History (Issue #102) ---

class SpoolUsageEntry(BaseModel):
    type: str  # "print_job" or "order"
    id: int
    name: str
    filament_used_g: float
    date: datetime | None
    status: str


class SpoolUsageResponse(BaseModel):
    spool_id: int
    total_weight_g: float
    remaining_weight_g: float
    total_consumed_g: float
    entries: list[SpoolUsageEntry]
