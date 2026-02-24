"""
CSV export endpoints for data portability (Issue #92).

Each endpoint exports all records for the current tenant as a UTF-8 CSV
with a BOM so Excel opens it correctly without an import wizard.

Security: all string values are passed through _sanitize() to prevent
CSV injection (Excel/Sheets formula execution via =, +, -, @ prefixes).
"""
import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.middleware.tenant import get_current_user, get_tenant_db
from app.middleware.tenant import SimpleUser as User
from app.models.filament import Spool
from app.models.hardware import HardwareItem
from app.models.order import Order, OrderSpool
from app.models.print_job import PrintJob, PrintJobSpool
from app.models.project import Project

router = APIRouter(prefix="/export", tags=["Export"])


def _sanitize(value) -> str:
    """Prevent CSV injection by prefixing formula-starting characters."""
    if value is None:
        return ""
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s
    return s


def _csv_response(rows: list[list], filename: str) -> StreamingResponse:
    output = io.StringIO()
    writer = csv.writer(output)
    for row in rows:
        writer.writerow(row)
    output.seek(0)
    # utf-8-sig adds BOM so Excel auto-detects encoding
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/spools.csv")
def export_spools(
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    spools = (
        db.query(Spool)
        .options(joinedload(Spool.filament_type), joinedload(Spool.manufacturer))
        .order_by(Spool.created_at)
        .all()
    )
    rows: list[list] = [[
        "Tracking ID", "Color", "Filament Type", "Manufacturer",
        "Total (g)", "Remaining (g)", "Remaining %",
        "Cost/kg", "Purchase Price", "Purchase Date",
        "Location", "Notes", "Active",
    ]]
    for s in spools:
        rows.append([
            _sanitize(s.tracking_id),
            _sanitize(s.color_name),
            _sanitize(s.filament_type.name),
            _sanitize(s.manufacturer.name),
            s.total_weight_g,
            s.remaining_weight_g,
            round(s.remaining_percent, 1),
            s.cost_per_kg,
            s.purchase_price,
            s.purchase_date.date() if s.purchase_date else "",
            _sanitize(s.location),
            _sanitize(s.notes),
            "Yes" if s.is_active else "No",
        ])
    return _csv_response(rows, "spools.csv")


@router.get("/print-jobs.csv")
def export_print_jobs(
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    jobs = (
        db.query(PrintJob)
        .options(
            joinedload(PrintJob.print_job_spools).joinedload(PrintJobSpool.spool),
            joinedload(PrintJob.spool),
            joinedload(PrintJob.project),
        )
        .order_by(PrintJob.printed_at.desc(), PrintJob.created_at.desc())
        .all()
    )
    rows: list[list] = [[
        "Date", "Name", "Status", "Filament Used (g)", "Print Time (min)",
        "Customer Job", "Customer Name", "Quoted Price", "Notes", "Spools",
    ]]
    for j in jobs:
        if j.print_job_spools:
            total_g = sum(pjs.filament_used_g for pjs in j.print_job_spools)
            spools_summary = "; ".join(
                f"{(pjs.spool.tracking_id or pjs.spool.color_name or 'Unknown')} {pjs.filament_used_g:.0f}g"
                for pjs in j.print_job_spools
                if pjs.spool
            )
        else:
            total_g = j.filament_used_g or 0
            spools_summary = (j.spool.tracking_id or j.spool.color_name or "") if j.spool else ""
        date = j.printed_at or j.created_at
        rows.append([
            date.date() if date else "",
            _sanitize(j.name),
            j.status,
            round(total_g, 2),
            j.print_time_minutes if j.print_time_minutes is not None else "",
            "Yes" if j.was_for_customer else "No",
            _sanitize(j.customer_name),
            j.quoted_price if j.quoted_price is not None else "",
            _sanitize(j.notes),
            _sanitize(spools_summary),
        ])
    return _csv_response(rows, "print-jobs.csv")


@router.get("/orders.csv")
def export_orders(
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    orders = (
        db.query(Order)
        .options(
            joinedload(Order.project),
            joinedload(Order.order_spools).joinedload(OrderSpool.spool),
            joinedload(Order.spool),
        )
        .order_by(Order.created_at.desc())
        .all()
    )
    rows: list[list] = [[
        "Order ID", "Date", "Customer", "Contact", "Location",
        "Item", "Status", "Quoted Price", "Shipping", "Due Date", "Notes", "Filament Spools",
    ]]
    for o in orders:
        item = o.custom_name or (o.project.name if o.project else "")
        if o.order_spools:
            spools_summary = "; ".join(
                f"{(os.spool.tracking_id or os.spool.color_name or 'Unknown')} {os.filament_grams:.0f}g"
                for os in o.order_spools
                if os.spool
            )
        elif o.spool:
            spools_summary = o.spool.tracking_id or o.spool.color_name or ""
        else:
            spools_summary = ""
        rows.append([
            o.id,
            o.created_at.date(),
            _sanitize(o.customer_name),
            _sanitize(o.customer_contact),
            _sanitize(o.customer_location),
            _sanitize(item),
            o.status,
            o.quoted_price if o.quoted_price is not None else "",
            o.shipping_charge if o.shipping_charge is not None else "",
            o.due_date.date() if o.due_date else "",
            _sanitize(o.notes),
            _sanitize(spools_summary),
        ])
    return _csv_response(rows, "orders.csv")


@router.get("/hardware.csv")
def export_hardware(
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    items = db.query(HardwareItem).order_by(HardwareItem.name).all()
    rows: list[list] = [[
        "Name", "Brand", "Purchase Price", "Qty Purchased",
        "Qty In Stock", "Cost/Item", "Purchase URL", "Notes",
    ]]
    for h in items:
        rows.append([
            _sanitize(h.name),
            _sanitize(h.brand),
            h.purchase_price,
            h.quantity_purchased,
            h.quantity_in_stock,
            round(h.cost_per_item, 4),
            _sanitize(h.purchase_url),
            _sanitize(h.notes),
        ])
    return _csv_response(rows, "hardware.csv")


@router.get("/projects.csv")
def export_projects(
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    projects_list = (
        db.query(Project)
        .options(joinedload(Project.project_filaments))
        .order_by(Project.name)
        .all()
    )
    rows: list[list] = [[
        "Name", "Filament (g)", "Print Time (h)", "Sell Price",
        "Model URL", "Active", "Notes",
    ]]
    for p in projects_list:
        filament_g = (
            round(sum(pf.grams for pf in p.project_filaments), 2)
            if p.project_filaments
            else (p.filament_grams if p.filament_grams is not None else "")
        )
        rows.append([
            _sanitize(p.name),
            filament_g,
            p.print_time_hours if p.print_time_hours is not None else "",
            p.sell_price if p.sell_price is not None else "",
            _sanitize(p.model_url),
            "Yes" if p.is_active else "No",
            _sanitize(p.notes),
        ])
    return _csv_response(rows, "projects.csv")
