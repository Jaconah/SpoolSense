from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.filament import SpoolResponse


class PrintJobSpoolInput(BaseModel):
    """Input schema for a single spool entry in a multi-color print job."""
    spool_id: int = Field(..., gt=0)
    filament_used_g: float = Field(..., gt=0)
    position: int = Field(..., ge=1, le=6)


class PrintJobSpoolResponse(BaseModel):
    """Response schema for a single spool entry in a multi-color print job."""
    id: int
    spool_id: int
    spool: SpoolResponse
    filament_used_g: float
    position: int

    model_config = {"from_attributes": True}


class PrintJobBase(BaseModel):
    # DEPRECATED: Use spools list instead (backward compatibility)
    spool_id: int | None = None
    filament_used_g: float | None = Field(None, ge=0)

    # Multi-color support (new)
    spools: list[PrintJobSpoolInput] | None = Field(None, min_length=1, max_length=6)

    project_id: int | None = None
    order_id: int | None = None
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    print_time_minutes: int | None = Field(None, ge=0)
    status: str = Field(default="completed", pattern=r"^(completed|failed|cancelled)$")
    was_for_customer: bool = False
    customer_name: str | None = Field(None, max_length=100)
    quoted_price: float | None = None
    notes: str | None = Field(None, max_length=1000)
    printed_at: datetime | None = None

    @field_validator('spools')
    @classmethod
    def validate_unique_positions(cls, v):
        """Ensure all spool positions are unique."""
        if v is None:
            return v
        positions = [s.position for s in v]
        if len(positions) != len(set(positions)):
            raise ValueError("Spool positions must be unique")
        return v


class PrintJobCreate(PrintJobBase):
    force: bool = Field(default=False, description="Allow bypassing spool shortage warnings (Issue #17)")

    @model_validator(mode='after')
    def validate_spool_data(self):
        """Ensure either spool_id or spools is provided, not both."""
        spool_id = self.spool_id
        spools = self.spools

        # At least one must be provided
        if not spool_id and not spools:
            raise ValueError("Either spool_id or spools must be provided")

        # Can't provide both
        if spool_id and spools:
            raise ValueError("Cannot provide both spool_id and spools")

        return self


class PrintJobUpdate(BaseModel):
    spool_id: int | None = None
    project_id: int | None = None
    order_id: int | None = None
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    filament_used_g: float | None = Field(None, ge=0)
    print_time_minutes: int | None = Field(None, ge=0)
    status: str | None = Field(None, pattern=r"^(completed|failed|cancelled)$")
    was_for_customer: bool | None = None
    customer_name: str | None = Field(None, max_length=100)
    quoted_price: float | None = None
    notes: str | None = Field(None, max_length=1000)
    printed_at: datetime | None = None
    # If provided, replaces all PrintJobSpool entries (multi-color update, Issue #78)
    spools: list[PrintJobSpoolInput] | None = None
    force: bool = Field(default=False, description="Allow bypassing spool shortage warnings (Issue #17)")


class PrintJobResponse(BaseModel):
    id: int
    project_id: int | None
    order_id: int | None
    name: str
    description: str | None
    print_time_minutes: int | None
    status: str
    was_for_customer: bool
    customer_name: str | None
    quoted_price: float | None
    notes: str | None
    printed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Multi-color support (new)
    print_job_spools: list[PrintJobSpoolResponse] = Field(default_factory=list)

    # DEPRECATED: Backward compatibility (will be None for new multi-color jobs)
    spool_id: int | None = None
    spool: SpoolResponse | None = None
    filament_used_g: float | None = None

    model_config = {"from_attributes": True}
