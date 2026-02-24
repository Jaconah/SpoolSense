from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.filament import Spool
    from app.models.hardware import HardwareItem
    from app.models.print_job import PrintJob


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True, index=True
    )
    spool_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("spools.id"), nullable=True, index=True
    )
    custom_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    custom_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    customer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    customer_contact: Mapped[str | None] = mapped_column(String(300), nullable=True)
    customer_location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="ordered")
    quoted_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    shipping_charge: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Snapshots of project template values at order creation time
    filament_grams_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)
    print_time_hours_snapshot: Mapped[float | None] = mapped_column(Float, nullable=True)

    project: Mapped["Project | None"] = relationship(back_populates="orders")
    # DEPRECATED: Use order_spools relationship instead (backward compatibility only)
    spool: Mapped["Spool | None"] = relationship("Spool", foreign_keys=[spool_id])

    # Multi-color support (new)
    order_spools: Mapped[list["OrderSpool"]] = relationship(
        "OrderSpool",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderSpool.position"
    )

    order_hardware: Mapped[list["OrderHardware"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    print_jobs: Mapped[list["PrintJob"]] = relationship(back_populates="order")


class OrderSpool(Base):
    """Junction table for many-to-many relationship between Orders and Spools.

    Similar to OrderHardware, stores cost snapshot for accurate P&L tracking."""
    __tablename__ = "order_spools"
    __table_args__ = (
        CheckConstraint('position >= 1 AND position <= 6', name='check_order_spool_position'),
        UniqueConstraint('order_id', 'position', name='uq_order_spool_position'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    spool_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("spools.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    filament_grams: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-6 for color order
    cost_per_kg_snapshot: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="order_spools")
    spool: Mapped["Spool"] = relationship("Spool")


class OrderHardware(Base):
    __tablename__ = "order_hardware"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hardware_item_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("hardware_items.id"), nullable=True, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_cost_snapshot: Mapped[float] = mapped_column(Float, default=0.0)
    hardware_name_snapshot: Mapped[str | None] = mapped_column(String(200), nullable=True)
    hardware_brand_snapshot: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # One-off hardware (items not tracked in inventory)
    is_one_off: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    one_off_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    one_off_cost: Mapped[float | None] = mapped_column(Float, nullable=True)

    order: Mapped["Order"] = relationship(back_populates="order_hardware")
    hardware_item: Mapped["HardwareItem | None"] = relationship(back_populates="order_hardware")
