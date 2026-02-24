from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.filament import Spool
    from app.models.order import Order
    from app.models.project import Project


class PrintJobSpool(Base):
    """Junction table for many-to-many relationship between PrintJobs and Spools."""
    __tablename__ = "print_job_spools"
    __table_args__ = (
        CheckConstraint('position >= 1 AND position <= 6', name='check_print_job_spool_position'),
        UniqueConstraint('print_job_id', 'position', name='uq_print_job_spool_position'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    print_job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("print_jobs.id", ondelete="CASCADE"), nullable=False
    )
    spool_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("spools.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    filament_used_g: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-6 for color order

    # Relationships
    print_job: Mapped["PrintJob"] = relationship("PrintJob", back_populates="print_job_spools")
    spool: Mapped["Spool"] = relationship("Spool")


class PrintJob(Base, TimestampMixin):
    __tablename__ = "print_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # DEPRECATED: Use print_job_spools relationship instead (backward compatibility only)
    spool_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("spools.id"), nullable=True, index=True
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    order_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # DEPRECATED: Use print_job_spools relationship instead (backward compatibility only)
    filament_used_g: Mapped[float | None] = mapped_column(Float, default=0.0, nullable=True)
    print_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="completed"
    )  # completed, failed, cancelled
    was_for_customer: Mapped[bool] = mapped_column(Boolean, default=False)
    customer_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    quoted_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    printed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Multi-color support (new)
    print_job_spools: Mapped[list["PrintJobSpool"]] = relationship(
        "PrintJobSpool",
        back_populates="print_job",
        cascade="all, delete-orphan",
        order_by="PrintJobSpool.position"
    )

    # Backward compatibility relationships (deprecated)
    spool: Mapped["Spool | None"] = relationship("Spool", foreign_keys=[spool_id])
    project: Mapped["Project | None"] = relationship("Project")
    order: Mapped["Order | None"] = relationship(back_populates="print_jobs")
