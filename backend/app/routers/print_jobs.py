import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.middleware.tenant import get_current_user, get_tenant_db
from app.middleware.tenant import SimpleUser as User
from app.models.filament import Spool
from app.models.print_job import PrintJob, PrintJobSpool
from app.models.product_on_hand import ProductOnHand
from app.models.project import Project
from app.models.settings import AppSettings
from app.schemas.common import PaginatedResponse
from app.schemas.print_job import PrintJobCreate, PrintJobResponse, PrintJobUpdate
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.filament import SpoolShortageResponse, SpoolValidationResponse
from app.services.spool_validator import validate_spool_inventory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/print-jobs", tags=["Print Jobs"])


def _deduct_spool(spool: Spool, grams: float, prevent_negative: bool) -> None:
    """Deduct filament from spool. Clamps to 0 when prevention is on; allows negatives when off."""
    if prevent_negative:
        spool.remaining_weight_g = max(0.0, spool.remaining_weight_g - grams)
    else:
        spool.remaining_weight_g -= grams


@router.get("", response_model=PaginatedResponse[PrintJobResponse])
def list_print_jobs(
    status: str | None = Query(None),
    was_for_customer: bool | None = Query(None),
    spool_id: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user),
):
    query = db.query(PrintJob)
    if status is not None:
        query = query.filter(PrintJob.status == status)
    if was_for_customer is not None:
        query = query.filter(PrintJob.was_for_customer == was_for_customer)
    if spool_id is not None:
        # Support filtering by spool in multi-color jobs
        query = query.filter(
            (PrintJob.spool_id == spool_id) |
            (PrintJob.print_job_spools.any(PrintJobSpool.spool_id == spool_id))
        )
    if search:
        term = f"%{search}%"
        query = query.filter(or_(
            PrintJob.name.ilike(term),
            PrintJob.description.ilike(term),
            PrintJob.customer_name.ilike(term),
            PrintJob.notes.ilike(term),
        ))
    total = query.count()
    items = (
        query
        .options(
            # Multi-color support
            joinedload(PrintJob.print_job_spools)
            .joinedload(PrintJobSpool.spool)
            .joinedload(Spool.filament_type),
            joinedload(PrintJob.print_job_spools)
            .joinedload(PrintJobSpool.spool)
            .joinedload(Spool.manufacturer),
            # Backward compatibility
            joinedload(PrintJob.spool).joinedload(Spool.filament_type),
            joinedload(PrintJob.spool).joinedload(Spool.manufacturer),
        )
        .order_by(PrintJob.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.post("", response_model=PrintJobResponse, status_code=201)
def create_print_job(data: PrintJobCreate, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    # Determine if using old format (single spool) or new format (multi-spool)
    if data.spools:
        # New multi-color format
        return _create_multicolor_print_job(data, db)
    elif data.spool_id:
        # Old single-spool format (backward compatibility)
        return _create_single_spool_print_job(data, db)
    else:
        raise HTTPException(status_code=400, detail="Either spool_id or spools must be provided")


def _create_single_spool_print_job(data: PrintJobCreate, db: Session) -> PrintJob:
    """Create print job using old single-spool format (backward compatibility)."""
    spool = db.query(Spool).filter(Spool.id == data.spool_id).first()
    if not spool:
        raise HTTPException(status_code=400, detail="Spool not found")

    # Validate inventory for completed jobs (unless force=True)
    if data.status == "completed" and data.filament_used_g and data.filament_used_g > 0:
        if not data.force:
            validation = validate_spool_inventory(
                db,
                [(data.spool_id, data.filament_used_g)]
            )

            if not validation.is_valid:
                # Return validation error (frontend will show warning dialog)
                raise HTTPException(
                    status_code=422,  # Unprocessable Entity
                    detail={
                        "type": "spool_shortage",
                        "validation": SpoolValidationResponse(
                            is_valid=False,
                            has_warnings=True,
                            shortages=[
                                SpoolShortageResponse(
                                    spool_id=s.spool_id,
                                    tracking_id=s.tracking_id,
                                    color_name=s.color_name,
                                    filament_type_name=s.filament_type_name,
                                    manufacturer_name=s.manufacturer_name,
                                    current_weight_g=s.current_weight_g,
                                    requested_weight_g=s.requested_weight_g,
                                    resulting_weight_g=s.resulting_weight_g,
                                    shortage_g=s.shortage_g
                                )
                                for s in validation.shortages
                            ],
                            message="One or more spools have insufficient inventory"
                        ).model_dump()
                    }
                )

    job = PrintJob(**data.model_dump(exclude={'spools', 'force'}))
    db.add(job)

    # Auto-subtract filament from spool for completed jobs
    if data.status == "completed" and data.filament_used_g and data.filament_used_g > 0:
        settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
        prevent = settings.enable_spool_negative_prevention if settings else True
        _deduct_spool(spool, data.filament_used_g, prevent)

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to create single-spool print job for spool %s", data.spool_id, exc_info=True)
        raise
    db.refresh(job)
    return job


def _create_multicolor_print_job(data: PrintJobCreate, db: Session) -> PrintJob:
    """Create print job using new multi-spool format."""
    # Validate all spools exist
    for spool_entry in data.spools:
        spool = db.query(Spool).filter(Spool.id == spool_entry.spool_id).first()
        if not spool:
            raise HTTPException(
                status_code=400,
                detail=f"Spool #{spool_entry.spool_id} not found"
            )

    # Validate inventory for completed jobs (unless force=True)
    if data.status == "completed" and not data.force:
        spool_usages = [
            (spool_entry.spool_id, spool_entry.filament_used_g)
            for spool_entry in data.spools
        ]
        validation = validate_spool_inventory(db, spool_usages)

        if not validation.is_valid:
            # Return validation error (frontend will show warning dialog)
            raise HTTPException(
                status_code=422,  # Unprocessable Entity
                detail={
                    "type": "spool_shortage",
                    "validation": SpoolValidationResponse(
                        is_valid=False,
                        has_warnings=True,
                        shortages=[
                            SpoolShortageResponse(
                                spool_id=s.spool_id,
                                tracking_id=s.tracking_id,
                                color_name=s.color_name,
                                filament_type_name=s.filament_type_name,
                                manufacturer_name=s.manufacturer_name,
                                current_weight_g=s.current_weight_g,
                                requested_weight_g=s.requested_weight_g,
                                resulting_weight_g=s.resulting_weight_g,
                                shortage_g=s.shortage_g
                            )
                            for s in validation.shortages
                        ],
                        message="One or more spools have insufficient inventory"
                    ).model_dump()
                }
            )

    # Create the print job
    job = PrintJob(**data.model_dump(exclude={'spool_id', 'filament_used_g', 'spools', 'force'}))
    db.add(job)
    db.flush()  # Get job ID

    # Create PrintJobSpool records and deduct inventory
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    prevent = settings.enable_spool_negative_prevention if settings else True
    for spool_entry in data.spools:
        pjs = PrintJobSpool(
            print_job_id=job.id,
            spool_id=spool_entry.spool_id,
            filament_used_g=spool_entry.filament_used_g,
            position=spool_entry.position
        )
        db.add(pjs)

        # Deduct inventory for completed jobs
        if data.status == "completed":
            spool = db.query(Spool).filter(Spool.id == spool_entry.spool_id).first()
            _deduct_spool(spool, spool_entry.filament_used_g, prevent)

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to create multi-color print job", exc_info=True)
        raise
    db.refresh(job)
    return job


@router.get("/{job_id}", response_model=PrintJobResponse)
def get_print_job(job_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    job = (
        db.query(PrintJob)
        .options(
            # Multi-color support
            joinedload(PrintJob.print_job_spools)
            .joinedload(PrintJobSpool.spool)
            .joinedload(Spool.filament_type),
            joinedload(PrintJob.print_job_spools)
            .joinedload(PrintJobSpool.spool)
            .joinedload(Spool.manufacturer),
            # Backward compatibility
            joinedload(PrintJob.spool).joinedload(Spool.filament_type),
            joinedload(PrintJob.spool).joinedload(Spool.manufacturer),
        )
        .filter(PrintJob.id == job_id)
        .first()
    )
    if not job:
        raise HTTPException(status_code=404, detail="Print job not found")
    return job


@router.put("/{job_id}", response_model=PrintJobResponse)
def update_print_job(
    job_id: int, data: PrintJobUpdate, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)
):
    job = db.query(PrintJob).options(
        joinedload(PrintJob.print_job_spools)
    ).filter(PrintJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Print job not found")

    update_data = data.model_dump(exclude_unset=True)
    spools_was_set = "spools" in update_data
    spools_update = update_data.pop("spools", None)
    update_data.pop("force", None)

    # Handle multi-color spools replacement (Issue #78)
    if spools_was_set and spools_update is not None:
        # Restore filament from existing completed spools before replacing
        if job.status == "completed":
            if job.print_job_spools:
                for pjs in job.print_job_spools:
                    spool = db.query(Spool).filter(Spool.id == pjs.spool_id).first()
                    if spool:
                        spool.remaining_weight_g += pjs.filament_used_g
            elif job.spool_id and job.filament_used_g:
                spool = db.query(Spool).filter(Spool.id == job.spool_id).first()
                if spool:
                    spool.remaining_weight_g += job.filament_used_g

        # Delete old PrintJobSpool records
        for pjs in list(job.print_job_spools):
            db.delete(pjs)
        db.flush()

        # Validate new spools exist
        for spool_data in spools_update:
            if not db.query(Spool).filter(Spool.id == spool_data["spool_id"]).first():
                raise HTTPException(
                    status_code=400,
                    detail=f"Spool #{spool_data['spool_id']} not found"
                )

        # Determine resulting status
        new_status = update_data.get("status", job.status)

        # Validate inventory if job will be completed (unless force=True)
        if new_status == "completed" and not data.force:
            spool_usages = [(s["spool_id"], s["filament_used_g"]) for s in spools_update]
            validation = validate_spool_inventory(db, spool_usages)
            if not validation.is_valid:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "type": "spool_shortage",
                        "validation": SpoolValidationResponse(
                            is_valid=False,
                            has_warnings=True,
                            shortages=[
                                SpoolShortageResponse(
                                    spool_id=s.spool_id,
                                    tracking_id=s.tracking_id,
                                    color_name=s.color_name,
                                    filament_type_name=s.filament_type_name,
                                    manufacturer_name=s.manufacturer_name,
                                    current_weight_g=s.current_weight_g,
                                    requested_weight_g=s.requested_weight_g,
                                    resulting_weight_g=s.resulting_weight_g,
                                    shortage_g=s.shortage_g
                                )
                                for s in validation.shortages
                            ],
                            message="One or more spools have insufficient inventory"
                        ).model_dump()
                    }
                )

        # Create new PrintJobSpool records and deduct inventory if completed
        upd_settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
        upd_prevent = upd_settings.enable_spool_negative_prevention if upd_settings else True
        for spool_data in spools_update:
            pjs = PrintJobSpool(
                print_job_id=job.id,
                spool_id=spool_data["spool_id"],
                filament_used_g=spool_data["filament_used_g"],
                position=spool_data["position"],
            )
            db.add(pjs)

            if new_status == "completed":
                spool = db.query(Spool).filter(Spool.id == spool_data["spool_id"]).first()
                if spool:
                    _deduct_spool(spool, spool_data["filament_used_g"], upd_prevent)

    elif "filament_used_g" in update_data and job.status == "completed" and not job.print_job_spools:
        # Legacy single-spool: handle filament_used_g changes
        spool = db.query(Spool).filter(Spool.id == job.spool_id).first()
        if spool:
            old_used = job.filament_used_g or 0
            new_used = update_data["filament_used_g"]
            net_change = new_used - old_used

            if net_change > 0 and not data.force:
                validation = validate_spool_inventory(
                    db,
                    [(job.spool_id, net_change)]
                )

                if not validation.is_valid:
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "type": "spool_shortage",
                            "validation": SpoolValidationResponse(
                                is_valid=False,
                                has_warnings=True,
                                shortages=[
                                    SpoolShortageResponse(
                                        spool_id=s.spool_id,
                                        tracking_id=s.tracking_id,
                                        color_name=s.color_name,
                                        filament_type_name=s.filament_type_name,
                                        manufacturer_name=s.manufacturer_name,
                                        current_weight_g=s.current_weight_g,
                                        requested_weight_g=s.requested_weight_g,
                                        resulting_weight_g=s.resulting_weight_g,
                                        shortage_g=s.shortage_g
                                    )
                                    for s in validation.shortages
                                ],
                                message="One or more spools have insufficient inventory"
                            ).model_dump()
                        }
                    )

            leg_settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
            leg_prevent = leg_settings.enable_spool_negative_prevention if leg_settings else True
            _deduct_spool(spool, new_used - old_used, leg_prevent)

    if "spool_id" in update_data:
        if not db.query(Spool).filter(Spool.id == update_data["spool_id"]).first():
            raise HTTPException(status_code=400, detail="Spool not found")

    for key, value in update_data.items():
        setattr(job, key, value)

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to update print job %s", job_id, exc_info=True)
        raise
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=204)
def delete_print_job(job_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    job = db.query(PrintJob).options(
        joinedload(PrintJob.print_job_spools)
    ).filter(PrintJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Print job not found")

    # Check if linked to Product on Hand
    linked_product = db.scalars(
        select(ProductOnHand).where(ProductOnHand.print_job_id == job_id)
    ).first()

    if linked_product:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete - print job is linked to Product on Hand #{linked_product.id}"
        )

    # Restore filament to spools if job was completed
    if job.status == "completed":
        # Multi-color job (new format)
        if job.print_job_spools:
            for pjs in job.print_job_spools:
                spool = db.query(Spool).filter(Spool.id == pjs.spool_id).first()
                if spool:
                    spool.remaining_weight_g += pjs.filament_used_g

        # Single-spool job (old format, backward compatibility)
        elif job.spool_id and job.filament_used_g and job.filament_used_g > 0:
            spool = db.query(Spool).filter(Spool.id == job.spool_id).first()
            if spool:
                spool.remaining_weight_g += job.filament_used_g

    db.delete(job)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to delete print job %s", job_id, exc_info=True)
        raise


@router.post("/{job_id}/convert-to-project", response_model=ProjectResponse, status_code=201)
def convert_print_job_to_project(
    job_id: int,
    data: ProjectCreate,
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user)
):
    """Convert a print job into a reusable project template.

    For multi-color jobs (with print_job_spools), creates ProjectFilament entries
    for each spool's filament type instead of setting a single filament_grams value
    on the project (Issue #79).
    """
    job = db.query(PrintJob).options(
        joinedload(PrintJob.print_job_spools).joinedload(PrintJobSpool.spool)
    ).filter(PrintJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Print job not found")

    # Create project from print job data
    # Use provided data from request, falling back to print job values
    project = Project(
        name=data.name,  # User provides name
        model_url=data.model_url,
        filament_grams=data.filament_grams if data.filament_grams is not None else job.filament_used_g,
        print_time_hours=data.print_time_hours if data.print_time_hours is not None else (
            job.print_time_minutes / 60.0 if job.print_time_minutes else None
        ),
        sell_price=data.sell_price,
        description=data.description or job.description,
        notes=data.notes or f"Created from print job: {job.name}",
        is_active=data.is_active,
    )

    db.add(project)
    db.flush()

    # For multi-color jobs, create ProjectFilament entries from print_job_spools (Issue #79)
    from app.models.project import ProjectFilament, ProjectHardware
    from app.models.hardware import HardwareItem

    if job.print_job_spools:
        for pjs in job.print_job_spools:
            if pjs.spool and pjs.spool.filament_type_id:
                pf = ProjectFilament(
                    project_id=project.id,
                    filament_type_id=pjs.spool.filament_type_id,
                    grams=pjs.filament_used_g,
                    position=pjs.position,
                )
                db.add(pf)

    # Add hardware if provided
    for hw in data.hardware:
        if not db.query(HardwareItem).filter(HardwareItem.id == hw.hardware_item_id).first():
            raise HTTPException(status_code=400, detail=f"Hardware item {hw.hardware_item_id} not found")
        ph = ProjectHardware(
            project_id=project.id,
            hardware_item_id=hw.hardware_item_id,
            quantity=hw.quantity,
        )
        db.add(ph)

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to convert print job %s to project", job_id, exc_info=True)
        raise
    db.refresh(project)

    # Reload with relationships
    return (
        db.query(Project)
        .options(
            joinedload(Project.hardware).joinedload(ProjectHardware.hardware_item),
            joinedload(Project.project_filaments),
        )
        .filter(Project.id == project.id)
        .first()
    )
