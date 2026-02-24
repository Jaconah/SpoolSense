from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.filament import FilamentType
    from app.models.hardware import HardwareItem
    from app.models.order import Order


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    model_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    filament_grams: Mapped[float | None] = mapped_column(Float, nullable=True)
    print_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    sell_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Multi-color support (new)
    project_filaments: Mapped[list["ProjectFilament"]] = relationship(
        "ProjectFilament",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectFilament.position"
    )

    hardware: Mapped[list["ProjectHardware"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="project")


class ProjectFilament(Base):
    """Junction table for many-to-many relationship between Projects and FilamentTypes.

    Projects are templates, so they specify filament TYPE requirements (e.g., "50g PLA"),
    not specific spools. Users select actual spools when creating orders."""
    __tablename__ = "project_filaments"
    __table_args__ = (
        CheckConstraint('position >= 1 AND position <= 6', name='check_project_filament_position'),
        UniqueConstraint('project_id', 'position', name='uq_project_filament_position'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    filament_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("filament_types.id"), nullable=False
    )
    grams: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-6 for color order
    color_note: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g., "Base color", "Accents"

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="project_filaments")
    filament_type: Mapped["FilamentType"] = relationship("FilamentType")


class ProjectHardware(Base):
    __tablename__ = "project_hardware"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    hardware_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hardware_items.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    project: Mapped["Project"] = relationship(back_populates="hardware")
    hardware_item: Mapped["HardwareItem"] = relationship(back_populates="project_hardware")
