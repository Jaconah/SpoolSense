from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.hardware import HardwareItemResponse


class ProjectHardwareBase(BaseModel):
    hardware_item_id: int
    quantity: int = Field(default=1, ge=1)


class ProjectHardwareResponse(ProjectHardwareBase):
    id: int
    hardware_item: HardwareItemResponse

    model_config = {"from_attributes": True}


class ProjectFilamentResponse(BaseModel):
    """Response schema for a single filament entry in a multi-color project template."""
    id: int
    filament_type_id: int
    grams: float
    position: int
    color_note: str | None = None

    model_config = {"from_attributes": True}


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    model_url: str | None = Field(None, max_length=500)
    filament_grams: float | None = Field(None, ge=0)
    print_time_hours: float | None = Field(None, ge=0)
    sell_price: float | None = Field(None, ge=0)
    description: str | None = Field(None, max_length=1000)
    notes: str | None = Field(None, max_length=1000)
    is_active: bool = True


class ProjectCreate(ProjectBase):
    hardware: list[ProjectHardwareBase] = []


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    model_url: str | None = Field(None, max_length=500)
    filament_grams: float | None = Field(None, ge=0)
    print_time_hours: float | None = Field(None, ge=0)
    sell_price: float | None = Field(None, ge=0)
    description: str | None = Field(None, max_length=1000)
    notes: str | None = Field(None, max_length=1000)
    is_active: bool | None = None
    hardware: list[ProjectHardwareBase] | None = None


class ProjectResponse(ProjectBase):
    id: int
    hardware: list[ProjectHardwareResponse]
    project_filaments: list[ProjectFilamentResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
