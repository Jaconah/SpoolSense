from sqlalchemy import Boolean, CheckConstraint, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class AppSettings(Base, TimestampMixin):
    __tablename__ = "app_settings"
    __table_args__ = (CheckConstraint("id = 1", name="singleton_check"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    currency_symbol: Mapped[str] = mapped_column(String(10), default="$")
    electricity_rate_kwh: Mapped[float] = mapped_column(Float, default=0.12)
    printer_wattage: Mapped[float] = mapped_column(Float, default=200.0)
    hourly_rate: Mapped[float] = mapped_column(Float, default=2.00)
    machine_depreciation_rate: Mapped[float] = mapped_column(Float, default=0.50)
    profit_margin_percent: Mapped[float] = mapped_column(Float, default=5.0)
    fixed_fee_per_order: Mapped[float] = mapped_column(Float, default=5.0)
    webhook_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    webhook_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    webhook_events: Mapped[str] = mapped_column(Text, default='["order_due"]')
    webhook_order_due_days: Mapped[int] = mapped_column(Integer, default=2)
    enable_shipping: Mapped[bool] = mapped_column(Boolean, default=False)
    default_shipping_charge: Mapped[float] = mapped_column(Float, default=0.0)
    low_spool_threshold_g: Mapped[float] = mapped_column(Float, default=50.0)
    show_spool_location: Mapped[bool] = mapped_column(Boolean, default=True)

    # Feature Module Toggles
    enable_hardware: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_projects: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_orders: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_products_on_hand: Mapped[bool] = mapped_column(Boolean, default=True)

    # Spool Validation Settings
    enable_spool_negative_prevention: Mapped[bool] = mapped_column(
        Boolean, default=True
    )
    minimum_spool_reserve_g: Mapped[float] = mapped_column(Float, default=5.0)

    # Behavior Toggles
    enable_low_spool_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    enable_tracking_id_auto_generation: Mapped[bool] = mapped_column(
        Boolean, default=True
    )

    # What's New tracking
    last_seen_version: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Self-hosted auth — bcrypt hash of owner password
    password_hash: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Auto-generated secrets (created on first run, persisted so tokens survive restarts)
    jwt_secret: Mapped[str | None] = mapped_column(String(128), nullable=True)
    app_secret: Mapped[str | None] = mapped_column(String(128), nullable=True)
