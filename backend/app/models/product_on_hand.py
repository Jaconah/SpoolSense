"""Product on Hand model - tracks finished products ready to sell."""
from sqlalchemy import Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from .base import Base, TimestampMixin


class ProductOnHand(Base, TimestampMixin):
    """Represents a finished product that is printed and ready to sell.

    Products on Hand are created from completed Print Jobs and linked to Projects.
    They track location, cost, and potential profit before being sold as Orders.
    """
    __tablename__ = "products_on_hand"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True
    )
    print_job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("print_jobs.id", ondelete="RESTRICT"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="completed")  # printed, completed
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["Project | None"] = relationship("Project")
    print_job: Mapped["PrintJob"] = relationship("PrintJob")
