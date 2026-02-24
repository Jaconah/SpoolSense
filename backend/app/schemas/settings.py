import json
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

VALID_WEBHOOK_EVENTS = frozenset({"order_due", "order_status_change", "low_stock"})


def _validate_webhook_events_str(v: str) -> str:
    try:
        events = json.loads(v)
    except (json.JSONDecodeError, TypeError):
        raise ValueError("webhook_events must be a valid JSON array string")
    if not isinstance(events, list):
        raise ValueError("webhook_events must be a JSON array")
    invalid = [e for e in events if e not in VALID_WEBHOOK_EVENTS]
    if invalid:
        raise ValueError(
            f"Unknown webhook events: {invalid}. "
            f"Valid values: {sorted(VALID_WEBHOOK_EVENTS)}"
        )
    return v


class SettingsBase(BaseModel):
    currency_symbol: str = Field(default="$", max_length=10)
    electricity_rate_kwh: float = Field(default=0.12, ge=0)
    printer_wattage: float = Field(default=200.0, ge=0)
    hourly_rate: float = Field(default=2.00, ge=0)
    machine_depreciation_rate: float = Field(default=0.50, ge=0)
    profit_margin_percent: float = Field(default=5.0, ge=0, le=100)
    fixed_fee_per_order: float = Field(default=5.0, ge=0)
    webhook_url: str | None = Field(None, max_length=500)
    webhook_enabled: bool = Field(default=False)
    webhook_events: str = Field(default='["order_due"]')
    webhook_order_due_days: int = Field(default=2, ge=1, le=30)

    @field_validator("webhook_events")
    @classmethod
    def validate_webhook_events(cls, v: str) -> str:
        return _validate_webhook_events_str(v)
    enable_shipping: bool = Field(default=False)
    default_shipping_charge: float = Field(default=0.0, ge=0)
    low_spool_threshold_g: float = Field(default=50.0, ge=0)
    show_spool_location: bool = Field(default=True)

    # Feature Module Toggles
    enable_hardware: bool = Field(default=True)
    enable_projects: bool = Field(default=True)
    enable_orders: bool = Field(default=True)
    enable_products_on_hand: bool = Field(default=True)

    # Spool Validation Settings
    enable_spool_negative_prevention: bool = Field(default=True)
    minimum_spool_reserve_g: float = Field(default=5.0, ge=0, le=100)

    # Behavior Toggles
    enable_low_spool_alerts: bool = Field(default=True)
    enable_tracking_id_auto_generation: bool = Field(default=True)

    # What's New tracking
    last_seen_version: str | None = None


class SettingsUpdate(BaseModel):
    currency_symbol: str | None = Field(None, max_length=10)
    electricity_rate_kwh: float | None = Field(None, ge=0)
    printer_wattage: float | None = Field(None, ge=0)
    hourly_rate: float | None = Field(None, ge=0)
    machine_depreciation_rate: float | None = Field(None, ge=0)
    profit_margin_percent: float | None = Field(None, ge=0, le=100)
    fixed_fee_per_order: float | None = Field(None, ge=0)
    webhook_url: str | None = Field(None, max_length=500)
    webhook_enabled: bool | None = None
    webhook_events: str | None = None
    webhook_order_due_days: int | None = Field(None, ge=1, le=30)

    @field_validator("webhook_events")
    @classmethod
    def validate_webhook_events(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _validate_webhook_events_str(v)
    enable_shipping: bool | None = None
    default_shipping_charge: float | None = Field(None, ge=0)
    low_spool_threshold_g: float | None = Field(None, ge=0)
    show_spool_location: bool | None = None

    # Feature Module Toggles
    enable_hardware: bool | None = None
    enable_projects: bool | None = None
    enable_orders: bool | None = None
    enable_products_on_hand: bool | None = None

    # Spool Validation Settings
    enable_spool_negative_prevention: bool | None = None
    minimum_spool_reserve_g: float | None = Field(None, ge=0, le=100)

    # Behavior Toggles
    enable_low_spool_alerts: bool | None = None
    enable_tracking_id_auto_generation: bool | None = None

    # What's New tracking
    last_seen_version: str | None = None


class SettingsResponse(SettingsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
