from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class FilamentType(Base, TimestampMixin):
    __tablename__ = "filament_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    abbreviation: Mapped[str] = mapped_column(String(10), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    spools: Mapped[list["Spool"]] = relationship(back_populates="filament_type")


class Manufacturer(Base, TimestampMixin):
    __tablename__ = "manufacturers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    spools: Mapped[list["Spool"]] = relationship(back_populates="manufacturer")


class Spool(Base, TimestampMixin):
    __tablename__ = "spools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filament_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("filament_types.id"), nullable=False, index=True
    )
    manufacturer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("manufacturers.id"), nullable=False, index=True
    )
    color_name: Mapped[str] = mapped_column(String(100), nullable=False)
    color_hex: Mapped[str] = mapped_column(String(7), default="#000000")
    total_weight_g: Mapped[float] = mapped_column(Float, default=1000.0)
    remaining_weight_g: Mapped[float] = mapped_column(Float, default=1000.0)
    cost_per_kg: Mapped[float] = mapped_column(Float, default=0.0)

    # Pricing fields (new schema)
    msrp: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # Customer pricing reference
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # What you paid (P&L)

    # Legacy pricing fields (kept for backwards compatibility during migration)
    normal_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_sale_price: Mapped[bool] = mapped_column(Boolean, default=False)

    purchase_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    tracking_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    filament_type: Mapped["FilamentType"] = relationship(back_populates="spools")
    manufacturer: Mapped["Manufacturer"] = relationship(back_populates="spools")
    print_jobs: Mapped[list["PrintJob"]] = relationship(back_populates="spool")

    @property
    def remaining_percent(self) -> float:
        if self.total_weight_g <= 0:
            return 0.0
        return round((self.remaining_weight_g / self.total_weight_g) * 100, 1)


# Import at bottom to avoid circular imports
from app.models.print_job import PrintJob  # noqa: E402
