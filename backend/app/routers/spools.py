import csv
import io
import logging
import random
import re
import string
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.middleware.tenant import get_current_user, get_tenant_db
from app.middleware.tenant import SimpleUser as User
from app.models.filament import FilamentType, Manufacturer, Spool
from app.models.order import Order, OrderSpool
from app.models.print_job import PrintJob, PrintJobSpool
from app.models.settings import AppSettings
from app.schemas.common import PaginatedResponse
from app.schemas.filament import (
    SpoolAdjust, SpoolCreate, SpoolResponse, SpoolUpdate,
    SpoolUsageEntry, SpoolUsageResponse,
)
from pydantic import BaseModel
from app.services.webhook_notifier import send_low_stock_webhook


class TrackingIdSuggestion(BaseModel):
    tracking_id: str

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/spools", tags=["Spools"])


def generate_tracking_id(abbreviation: str, db: Session) -> str:
    """
    Generate tracking ID like PLA01, ABS02, etc.
    Auto-expands from 2 digits (01-99) to 3 digits (100+) when needed.
    """
    prefix = abbreviation.upper()

    # Find the highest number for this prefix
    existing_spools = db.query(Spool).filter(
        Spool.tracking_id.like(f"{prefix}%")
    ).all()

    max_num = 0
    for spool in existing_spools:
        if spool.tracking_id and spool.tracking_id.startswith(prefix):
            try:
                # Extract the numeric part
                num_part = spool.tracking_id[len(prefix):]
                num = int(num_part)
                max_num = max(max_num, num)
            except (ValueError, IndexError):
                continue

    # Increment
    next_num = max_num + 1

    # Auto-expand: use 2 digits for 1-99, 3 digits for 100+
    if next_num < 100:
        return f"{prefix}{next_num:02d}"
    else:
        return f"{prefix}{next_num:03d}"


def check_tracking_id_duplicate(tracking_id: str, db: Session, exclude_spool_id: int | None = None):
    """
    Check if tracking ID already exists and return the existing spool info.
    Returns None if no duplicate, or dict with spool info if duplicate exists.
    """
    query = db.query(Spool).filter(Spool.tracking_id == tracking_id)
    if exclude_spool_id:
        query = query.filter(Spool.id != exclude_spool_id)

    existing_spool = query.options(
        joinedload(Spool.filament_type),
        joinedload(Spool.manufacturer)
    ).first()

    if existing_spool:
        return {
            "id": existing_spool.id,
            "tracking_id": existing_spool.tracking_id,
            "color_name": existing_spool.color_name,
            "remaining_weight_g": existing_spool.remaining_weight_g,
            "filament_type": existing_spool.filament_type.name,
            "manufacturer": existing_spool.manufacturer.name,
            "is_active": existing_spool.is_active
        }
    return None


@router.get("/suggest-tracking-id", response_model=TrackingIdSuggestion)
def suggest_tracking_id(
    filament_type_id: int = Query(..., description="Filament type ID to generate tracking ID for"),
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a suggested tracking ID for a given filament type."""
    filament_type = db.query(FilamentType).filter(FilamentType.id == filament_type_id).first()
    if not filament_type:
        raise HTTPException(status_code=404, detail="Filament type not found")

    suggested_id = generate_tracking_id(filament_type.abbreviation, db)
    return TrackingIdSuggestion(tracking_id=suggested_id)


@router.get("", response_model=PaginatedResponse[SpoolResponse])
def list_spools(
    is_active: bool | None = Query(None),
    filament_type_id: int | None = Query(None),
    manufacturer_id: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Spool)
    if is_active is not None:
        query = query.filter(Spool.is_active == is_active)
    if filament_type_id is not None:
        query = query.filter(Spool.filament_type_id == filament_type_id)
    if manufacturer_id is not None:
        query = query.filter(Spool.manufacturer_id == manufacturer_id)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(
            Spool.color_name.ilike(term),
            Spool.tracking_id.ilike(term),
            Spool.location.ilike(term),
            Spool.notes.ilike(term),
        ))
    total = query.count()
    items = (
        query
        .options(joinedload(Spool.filament_type), joinedload(Spool.manufacturer))
        .order_by(Spool.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.post("", response_model=SpoolResponse, status_code=201)
def create_spool(
    data: SpoolCreate,
    force_duplicate: bool = Query(False, description="Force creation even if tracking ID is duplicate"),
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user)
):
    # Validate foreign keys
    filament_type = db.query(FilamentType).filter(FilamentType.id == data.filament_type_id).first()
    if not filament_type:
        raise HTTPException(status_code=400, detail="Filament type not found")
    if not db.query(Manufacturer).filter(Manufacturer.id == data.manufacturer_id).first():
        raise HTTPException(status_code=400, detail="Manufacturer not found")

    spool_data = data.model_dump()

    # Auto-generate tracking ID if not provided
    if not spool_data.get('tracking_id'):
        spool_data['tracking_id'] = generate_tracking_id(filament_type.abbreviation, db)
    else:
        # Check for duplicate if manually provided
        duplicate_info = check_tracking_id_duplicate(spool_data['tracking_id'], db)
        if duplicate_info and not force_duplicate:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Tracking ID already in use",
                    "existing_spool": duplicate_info
                }
            )

    spool = Spool(**spool_data)
    db.add(spool)

    # Increment usage counts
    db.query(FilamentType).filter(FilamentType.id == data.filament_type_id).update(
        {FilamentType.usage_count: FilamentType.usage_count + 1}
    )
    db.query(Manufacturer).filter(Manufacturer.id == data.manufacturer_id).update(
        {Manufacturer.usage_count: Manufacturer.usage_count + 1}
    )

    # Security: Handle race condition - two simultaneous requests with same tracking_id
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if "tracking_id" in str(e):
            # Re-fetch duplicate info after rollback
            duplicate_info = check_tracking_id_duplicate(spool_data['tracking_id'], db)
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Tracking ID already in use",
                    "existing_spool": duplicate_info
                }
            )
        logger.error("Unexpected integrity error creating spool for user %s", current_user.id, exc_info=True)
        raise

    db.refresh(spool)
    return spool


@router.get("/{spool_id}", response_model=SpoolResponse)
def get_spool(spool_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    spool = (
        db.query(Spool)
        .options(joinedload(Spool.filament_type), joinedload(Spool.manufacturer))
        .filter(Spool.id == spool_id)
        .first()
    )
    if not spool:
        raise HTTPException(status_code=404, detail="Spool not found")
    return spool


@router.put("/{spool_id}", response_model=SpoolResponse)
def update_spool(
    spool_id: int,
    data: SpoolUpdate,
    background_tasks: BackgroundTasks,
    force_duplicate: bool = Query(False, description="Force update even if tracking ID is duplicate"),
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user)
):
    spool = db.query(Spool).filter(Spool.id == spool_id).first()
    if not spool:
        raise HTTPException(status_code=404, detail="Spool not found")
    update_data = data.model_dump(exclude_unset=True)
    if "filament_type_id" in update_data:
        if not db.query(FilamentType).filter(FilamentType.id == update_data["filament_type_id"]).first():
            raise HTTPException(status_code=400, detail="Filament type not found")
    if "manufacturer_id" in update_data:
        if not db.query(Manufacturer).filter(Manufacturer.id == update_data["manufacturer_id"]).first():
            raise HTTPException(status_code=400, detail="Manufacturer not found")

    # Check for duplicate tracking ID if being updated
    if "tracking_id" in update_data and update_data["tracking_id"] != spool.tracking_id:
        duplicate_info = check_tracking_id_duplicate(update_data["tracking_id"], db, exclude_spool_id=spool_id)
        if duplicate_info and not force_duplicate:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Tracking ID already in use",
                    "existing_spool": duplicate_info
                }
            )

    for key, value in update_data.items():
        setattr(spool, key, value)

    # Security: Handle race condition
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        if "tracking_id" in str(e) and "tracking_id" in update_data:
            # Re-fetch duplicate info after rollback
            duplicate_info = check_tracking_id_duplicate(update_data["tracking_id"], db, exclude_spool_id=spool_id)
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Tracking ID already in use",
                    "existing_spool": duplicate_info
                }
            )
        logger.error("Unexpected integrity error updating spool %s for user %s", spool_id, current_user.id, exc_info=True)
        raise

    db.refresh(spool)

    # Fire low_stock webhook if remaining weight fell below threshold
    if "remaining_weight_g" in update_data:
        settings_row = db.query(AppSettings).filter(AppSettings.id == 1).first()
        threshold = settings_row.low_spool_threshold_g if settings_row else 50.0
        if settings_row and settings_row.webhook_enabled and settings_row.webhook_url:
            import json as _json
            try:
                events = _json.loads(settings_row.webhook_events or "[]")
            except (ValueError, TypeError):
                events = []
            if "low_stock" in events and spool.remaining_weight_g < threshold:
                filament_type_name = getattr(spool.filament_type, "name", "") if spool.filament_type else ""
                label = f"{spool.color_name} {filament_type_name}".strip() or f"Spool #{spool.id}"
                background_tasks.add_task(
                    send_low_stock_webhook,
                    settings_row.webhook_url,
                    spool.id,
                    label,
                    spool.remaining_weight_g,
                    spool.tracking_id,
                )

    return spool


@router.delete("/{spool_id}", status_code=204)
def delete_spool(spool_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    spool = db.query(Spool).filter(Spool.id == spool_id).first()
    if not spool:
        raise HTTPException(status_code=404, detail="Spool not found")
    if spool.print_jobs:
        raise HTTPException(
            status_code=400, detail="Cannot delete: spool has associated print jobs"
        )
    if db.query(PrintJobSpool).filter(PrintJobSpool.spool_id == spool_id).first():
        raise HTTPException(
            status_code=400, detail="Cannot delete: spool is used in multi-color print jobs"
        )
    if db.query(OrderSpool).filter(OrderSpool.spool_id == spool_id).first():
        raise HTTPException(
            status_code=400, detail="Cannot delete: spool is used in multi-color orders"
        )
    db.delete(spool)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to delete spool %s for user %s", spool_id, current_user.id, exc_info=True)
        raise


@router.get("/{spool_id}/usage", response_model=SpoolUsageResponse)
def get_spool_usage(
    spool_id: int,
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    """Return all print jobs and orders that have consumed filament from this spool."""
    spool = db.query(Spool).filter(Spool.id == spool_id).first()
    if not spool:
        raise HTTPException(status_code=404, detail="Spool not found")

    entries: list[SpoolUsageEntry] = []

    # Print job usage via PrintJobSpool junction
    pj_usages = (
        db.query(PrintJobSpool)
        .options(joinedload(PrintJobSpool.print_job))
        .filter(PrintJobSpool.spool_id == spool_id)
        .all()
    )
    for pjs in pj_usages:
        pj = pjs.print_job
        entries.append(SpoolUsageEntry(
            type="print_job",
            id=pj.id,
            name=pj.name,
            filament_used_g=pjs.filament_used_g,
            date=pj.printed_at or pj.created_at,
            status=pj.status,
        ))

    # Order usage via OrderSpool junction
    order_usages = (
        db.query(OrderSpool)
        .options(joinedload(OrderSpool.order))
        .filter(OrderSpool.spool_id == spool_id)
        .all()
    )
    for os in order_usages:
        o = os.order
        name = o.custom_name or f"Order #{o.id}"
        if o.customer_name:
            name += f" — {o.customer_name}"
        entries.append(SpoolUsageEntry(
            type="order",
            id=o.id,
            name=name,
            filament_used_g=os.filament_grams,
            date=o.created_at,
            status=o.status,
        ))

    entries.sort(key=lambda e: e.date or datetime(1900, 1, 1), reverse=True)
    total_consumed = round(sum(e.filament_used_g for e in entries), 2)

    return SpoolUsageResponse(
        spool_id=spool_id,
        total_weight_g=spool.total_weight_g,
        remaining_weight_g=spool.remaining_weight_g,
        total_consumed_g=total_consumed,
        entries=entries,
    )


@router.patch("/{spool_id}/adjust", response_model=SpoolResponse)
def adjust_spool_weight(
    spool_id: int, data: SpoolAdjust, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)
):
    spool = db.query(Spool).filter(Spool.id == spool_id).first()
    if not spool:
        raise HTTPException(status_code=404, detail="Spool not found")
    spool.remaining_weight_g = data.remaining_weight_g
    db.commit()
    db.refresh(spool)
    return spool


@router.get("/alerts/low-and-empty", response_model=dict)
def get_low_and_empty_spools(
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get spools that are empty (0g) or below the low threshold.
    Returns separate lists for empty and low spools.
    """
    # Get the low threshold from settings (default to 50g if not set)
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    threshold = settings.low_spool_threshold_g if settings else 50.0

    # Get active spools that are empty or low
    empty_spools = db.query(Spool).options(
        joinedload(Spool.filament_type),
        joinedload(Spool.manufacturer)
    ).filter(
        Spool.is_active == True,
        Spool.remaining_weight_g == 0
    ).all()

    low_spools = db.query(Spool).options(
        joinedload(Spool.filament_type),
        joinedload(Spool.manufacturer)
    ).filter(
        Spool.is_active == True,
        Spool.remaining_weight_g > 0,
        Spool.remaining_weight_g <= threshold
    ).all()

    return {
        "threshold_g": threshold,
        "empty_spools": [
            {
                "id": spool.id,
                "tracking_id": spool.tracking_id,
                "color_name": spool.color_name,
                "filament_type": spool.filament_type.name,
                "manufacturer": spool.manufacturer.name,
                "remaining_weight_g": spool.remaining_weight_g
            }
            for spool in empty_spools
        ],
        "low_spools": [
            {
                "id": spool.id,
                "tracking_id": spool.tracking_id,
                "color_name": spool.color_name,
                "filament_type": spool.filament_type.name,
                "manufacturer": spool.manufacturer.name,
                "remaining_weight_g": spool.remaining_weight_g
            }
            for spool in low_spools
        ]
    }


# ============================================================================
# CSV Import (Issue #105)
# ============================================================================

MAX_IMPORT_SIZE = 5 * 1024 * 1024  # 5 MB — safety cap for CSV uploads (#124)

_TEMPLATE_CSV = (
    "filament_type,manufacturer,color_name,color_hex,total_weight_g,"
    "remaining_weight_g,cost_per_kg,purchase_date,location,notes,tracking_id\n"
    "PLA,Bambu Lab,Jade White,#F0EDE8,1000,850,19.99,2026-01-10,Shelf A,Example note,\n"
    "PETG,Polymaker,Galaxy Black,#1A1A1A,1000,1000,24.99,2026-01-15,,,\n"
    "ABS,eSUN,Fire Red,#FF2200,500,320,18.50,,,Needs drying,MY-CUSTOM-ID\n"
)


@router.get("/import/template")
def download_import_template(
    current_user: User = Depends(get_current_user),
):
    """Download a CSV template for bulk spool import."""
    return Response(
        content=_TEMPLATE_CSV,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=spool_import_template.csv"},
    )


def _derive_abbreviation(name: str) -> str:
    """Derive a short abbreviation from a filament type name (e.g. 'PLA' → 'PLA')."""
    letters = re.sub(r"[^A-Za-z]", "", name).upper()
    return letters[:4] if letters else name[:4].upper()


def _get_or_create_filament_type(db: Session, name: str) -> FilamentType:
    ft = db.query(FilamentType).filter(
        FilamentType.name.ilike(name.strip())
    ).first()
    if not ft:
        abbreviation = _derive_abbreviation(name.strip())
        ft = FilamentType(name=name.strip(), abbreviation=abbreviation)
        db.add(ft)
        db.flush()
    return ft


def _get_or_create_manufacturer(db: Session, name: str) -> Manufacturer:
    mfg = db.query(Manufacturer).filter(
        Manufacturer.name.ilike(name.strip())
    ).first()
    if not mfg:
        mfg = Manufacturer(name=name.strip())
        db.add(mfg)
        db.flush()
    return mfg


@router.post("/import")
async def import_spools_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bulk-import spools from a CSV file.

    Validates the entire CSV before writing anything.  If any row fails
    validation the whole upload is rejected with per-row error details and
    nothing is committed (#127).

    Required columns: filament_type, manufacturer, color_name, total_weight_g, cost_per_kg
    Optional columns: color_hex, remaining_weight_g, purchase_date, location, notes, tracking_id

    filament_type and manufacturer are matched case-insensitively and created if not found.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted")

    # Reject obviously non-text content types (images, PDFs, archives, etc.)
    # Allow text/*, application/csv, application/octet-stream (common browser defaults for CSV)
    if file.content_type:
        ct = file.content_type.split(";")[0].strip().lower()
        _REJECTED_PREFIXES = ("image/", "video/", "audio/")
        _REJECTED_TYPES = {"application/pdf", "application/zip", "application/x-zip-compressed",
                           "application/x-rar-compressed", "application/msword",
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
        if any(ct.startswith(p) for p in _REJECTED_PREFIXES) or ct in _REJECTED_TYPES:
            raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    if len(content) > MAX_IMPORT_SIZE:
        raise HTTPException(status_code=413, detail="CSV file exceeds the 5 MB limit")

    try:
        text = content.decode("utf-8-sig")  # handle BOM from Excel exports
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File encoding not supported. Please save your file as UTF-8 CSV and re-upload.",
        )

    # Sanity-check limits for numeric fields
    _MAX_WEIGHT_G = 1_000_000   # 1000 kg — no real spool exceeds this
    _MAX_COST_PER_KG = 10_000   # $10,000/kg — generous upper bound

    REQUIRED_COLS = ["filament_type", "manufacturer", "color_name", "total_weight_g", "cost_per_kg"]
    reader = csv.DictReader(io.StringIO(text))

    # Validate required columns exist in header
    fieldnames = reader.fieldnames or []
    missing = [c for c in REQUIRED_COLS if c not in fieldnames]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"CSV is missing required columns: {', '.join(missing)}",
        )

    # ------------------------------------------------------------------ #
    # Pass 1: validate every row (no DB writes — only reads).             #
    # Collect all errors so the user can fix them all in one go.          #
    # ------------------------------------------------------------------ #
    validated_rows: list[dict] = []
    errors: list[dict] = []
    seen_tracking_ids: set[str] = set()  # detect duplicates within this CSV

    for row_num, row in enumerate(reader, start=2):  # row 1 = header
        try:
            # Required fields
            ft_name = (row.get("filament_type") or "").strip()
            mfg_name = (row.get("manufacturer") or "").strip()
            color_name = (row.get("color_name") or "").strip()
            total_weight_raw = (row.get("total_weight_g") or "").strip()
            cost_raw = (row.get("cost_per_kg") or "").strip()

            if not ft_name:
                errors.append({"row": row_num, "reason": "filament_type is required"})
                continue
            if not mfg_name:
                errors.append({"row": row_num, "reason": "manufacturer is required"})
                continue
            if not color_name:
                errors.append({"row": row_num, "reason": "color_name is required"})
                continue
            if not total_weight_raw:
                errors.append({"row": row_num, "reason": "total_weight_g is required"})
                continue
            if not cost_raw:
                errors.append({"row": row_num, "reason": "cost_per_kg is required"})
                continue

            try:
                total_weight_g = float(total_weight_raw)
                if not (0 < total_weight_g <= _MAX_WEIGHT_G):
                    raise ValueError
            except ValueError:
                errors.append({"row": row_num, "reason": f"Invalid total_weight_g: '{total_weight_raw}' (must be between 0 and {_MAX_WEIGHT_G:,})"})
                continue

            try:
                cost_per_kg = float(cost_raw)
                if not (0 <= cost_per_kg <= _MAX_COST_PER_KG):
                    raise ValueError
            except ValueError:
                errors.append({"row": row_num, "reason": f"Invalid cost_per_kg: '{cost_raw}' (must be between 0 and {_MAX_COST_PER_KG:,})"})
                continue

            # Optional: remaining_weight_g
            remaining_raw = (row.get("remaining_weight_g") or "").strip()
            if remaining_raw:
                try:
                    remaining_weight_g = float(remaining_raw)
                    if not (0 <= remaining_weight_g <= _MAX_WEIGHT_G):
                        raise ValueError
                except ValueError:
                    errors.append({"row": row_num, "reason": f"Invalid remaining_weight_g: '{remaining_raw}' (must be between 0 and {_MAX_WEIGHT_G:,})"})
                    continue
            else:
                remaining_weight_g = total_weight_g

            # Optional: color_hex (validate format)
            color_hex_raw = (row.get("color_hex") or "").strip()
            if color_hex_raw:
                if not re.match(r"^#[0-9a-fA-F]{6}$", color_hex_raw):
                    errors.append({"row": row_num, "reason": f"Invalid color_hex value: '{color_hex_raw}'"})
                    continue
                color_hex = color_hex_raw
            else:
                color_hex = "#808080"

            # Optional: purchase_date
            purchase_date = None
            date_raw = (row.get("purchase_date") or "").strip()
            if date_raw:
                for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
                    try:
                        purchase_date = datetime.strptime(date_raw, fmt)
                        break
                    except ValueError:
                        continue
                if purchase_date is None:
                    errors.append({"row": row_num, "reason": f"Invalid purchase_date: '{date_raw}' (use YYYY-MM-DD)"})
                    continue

            location = (row.get("location") or "").strip()[:200] or None
            notes = (row.get("notes") or "").strip()[:1000] or None

            # Optional: tracking_id — validate for duplicates now (read-only)
            tracking_id_raw = (row.get("tracking_id") or "").strip()
            if tracking_id_raw:
                if tracking_id_raw in seen_tracking_ids:
                    errors.append({"row": row_num, "reason": f"tracking_id '{tracking_id_raw}' appears more than once in this CSV"})
                    continue
                dup = check_tracking_id_duplicate(tracking_id_raw, db)
                if dup:
                    errors.append({"row": row_num, "reason": f"tracking_id '{tracking_id_raw}' already exists"})
                    continue
                seen_tracking_ids.add(tracking_id_raw)

            validated_rows.append({
                "ft_name": ft_name,
                "mfg_name": mfg_name,
                "color_name": color_name,
                "total_weight_g": total_weight_g,
                "remaining_weight_g": remaining_weight_g,
                "cost_per_kg": cost_per_kg,
                "color_hex": color_hex,
                "purchase_date": purchase_date,
                "location": location,
                "notes": notes,
                "tracking_id_raw": tracking_id_raw,
            })

        except Exception as e:
            logger.warning("CSV import row %s error: %s", row_num, e, exc_info=True)
            errors.append({"row": row_num, "reason": f"Unexpected error: {e}"})

    # Reject the whole upload if any row failed — nothing written yet
    if errors:
        raise HTTPException(
            status_code=422,
            detail={"message": "CSV validation failed; no spools were imported.", "errors": errors},
        )

    # ------------------------------------------------------------------ #
    # Pass 2: all rows are valid — import atomically in one transaction.  #
    # ------------------------------------------------------------------ #
    imported = 0
    for vr in validated_rows:
        filament_type = _get_or_create_filament_type(db, vr["ft_name"])
        manufacturer = _get_or_create_manufacturer(db, vr["mfg_name"])

        tracking_id = vr["tracking_id_raw"] or generate_tracking_id(filament_type.abbreviation, db)

        spool = Spool(
            filament_type_id=filament_type.id,
            manufacturer_id=manufacturer.id,
            color_name=vr["color_name"],
            color_hex=vr["color_hex"],
            total_weight_g=vr["total_weight_g"],
            remaining_weight_g=vr["remaining_weight_g"],
            cost_per_kg=vr["cost_per_kg"],
            purchase_date=vr["purchase_date"],
            location=vr["location"],
            notes=vr["notes"],
            tracking_id=tracking_id,
            is_active=True,
        )
        db.add(spool)
        db.flush()  # flush so generate_tracking_id sees it for the next row

        filament_type.usage_count += 1
        manufacturer.usage_count += 1
        imported += 1

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("CSV import commit failed for user %s", current_user.id, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save imported spools")

    return {
        "imported": imported,
        "skipped": 0,
        "errors": [],
    }
