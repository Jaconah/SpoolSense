from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class HardwareItem(Base, TimestampMixin):
    __tablename__ = "hardware_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(200), nullable=True)
    purchase_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    purchase_price: Mapped[float] = mapped_column(Float, default=0.0)
    quantity_purchased: Mapped[int] = mapped_column(Integer, default=1)
    quantity_in_stock: Mapped[int] = mapped_column(Integer, default=0)
    low_stock_threshold: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    project_hardware: Mapped[list["ProjectHardware"]] = relationship(back_populates="hardware_item")
    order_hardware: Mapped[list["OrderHardware"]] = relationship(back_populates="hardware_item")

    @property
    def cost_per_item(self) -> float:
        if self.quantity_purchased <= 0:
            return 0.0
        return round(self.purchase_price / self.quantity_purchased, 4)

    @property
    def is_low_stock(self) -> bool:
        if self.low_stock_threshold is None:
            return False
        return self.quantity_in_stock <= self.low_stock_threshold


# Import at bottom to avoid circular imports
from app.models.project import ProjectHardware  # noqa: E402, F401
from app.models.order import OrderHardware  # noqa: E402, F401
