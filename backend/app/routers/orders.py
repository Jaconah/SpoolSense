import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.middleware.tenant import get_current_user, get_tenant_db
from app.middleware.tenant import SimpleUser as User
from app.models.filament import Spool
from app.models.hardware import HardwareItem
from app.models.order import Order, OrderHardware, OrderSpool
from app.models.print_job import PrintJobSpool
from app.models.print_job import PrintJob
from app.models.project import Project, ProjectHardware
from app.models.settings import AppSettings
from app.schemas.common import PaginatedResponse
from app.schemas.order import (
    OrderCreate,
    OrderInvoiceFilamentLine,
    OrderInvoiceHardwareLine,
    OrderInvoiceResponse,
    OrderProfitBreakdown,
    OrderResponse,
    OrderSummary,
    OrderUpdate,
)
from app.schemas.filament import SpoolShortageResponse, SpoolValidationResponse
from app.services.webhook_notifier import check_and_notify_overdue_orders, send_order_status_change_webhook
from app.services.spool_validator import validate_spool_inventory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])


def _deduct_spool(spool: Spool, grams: float, prevent_negative: bool) -> None:
    """Deduct filament from spool. Clamps to 0 when prevention is on; allows negatives when off."""
    if prevent_negative:
        spool.remaining_weight_g = max(0.0, spool.remaining_weight_g - grams)
    else:
        spool.remaining_weight_g -= grams


def _load_order(db: Session, order_id: int) -> Order:
    order = (
        db.query(Order)
        .options(
            joinedload(Order.order_hardware).joinedload(OrderHardware.hardware_item),
            joinedload(Order.project),
            joinedload(Order.spool),
            joinedload(Order.order_spools),
        )
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.get("/summary", response_model=OrderSummary)
def get_order_summary(db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    currency = settings.currency_symbol if settings else "$"

    total = db.query(func.count(Order.id)).scalar() or 0
    ordered = db.query(func.count(Order.id)).filter(Order.status == "ordered").scalar() or 0
    printed = db.query(func.count(Order.id)).filter(Order.status == "printed").scalar() or 0
    finished = db.query(func.count(Order.id)).filter(Order.status == "finished").scalar() or 0
    sold = db.query(func.count(Order.id)).filter(Order.status == "sold").scalar() or 0

    # Calculate total revenue including shipping
    total_revenue = 0.0
    sold_orders_for_revenue = db.query(Order).filter(Order.status == "sold").all()
    for order in sold_orders_for_revenue:
        total_revenue += (order.quoted_price or 0.0) + (order.shipping_charge or 0.0)

    # Calculate total cost for sold orders
    total_cost = 0.0
    sold_orders = (
        db.query(Order)
        .options(
            joinedload(Order.order_hardware),
            joinedload(Order.project),
            joinedload(Order.spool),
        )
        .filter(Order.status == "sold")
        .all()
    )
    for order in sold_orders:
        total_cost += _calculate_order_cost(order, settings)

    return OrderSummary(
        total_orders=total,
        ordered_orders=ordered,
        printed_orders=printed,
        finished_orders=finished,
        sold_orders=sold,
        total_revenue=round(total_revenue, 2),
        total_cost=round(total_cost, 2),
        total_profit=round(total_revenue - total_cost, 2),
        currency_symbol=currency,
    )


@router.get("", response_model=PaginatedResponse[OrderResponse])
def list_orders(
    status: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user),
):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(
            Order.customer_name.ilike(term),
            Order.customer_contact.ilike(term),
            Order.custom_name.ilike(term),
            Order.notes.ilike(term),
        ))
    total = query.count()
    items = (
        query
        .options(
            joinedload(Order.order_hardware).joinedload(OrderHardware.hardware_item),
            joinedload(Order.order_spools),
        )
        .order_by(Order.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(data: OrderCreate, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    order_data = data.model_dump(exclude={"hardware_items", "spools"})
    order = Order(**order_data)

    # Validate FKs and snapshot project values
    if order.project_id:
        project = db.query(Project).filter(Project.id == order.project_id).first()
        if not project:
            raise HTTPException(status_code=400, detail="Project not found")
        order.filament_grams_snapshot = project.filament_grams
        order.print_time_hours_snapshot = project.print_time_hours
    if order.spool_id:
        if not db.query(Spool).filter(Spool.id == order.spool_id).first():
            raise HTTPException(status_code=400, detail="Spool not found")

    db.add(order)
    db.flush()

    # Process multi-color order spools (Issue #76)
    if data.spools:
        positions = [s.position for s in data.spools]
        if len(positions) != len(set(positions)):
            raise HTTPException(status_code=400, detail="Duplicate spool positions are not allowed")
    for spool_input in data.spools:
        spool = db.query(Spool).filter(Spool.id == spool_input.spool_id).first()
        if not spool:
            raise HTTPException(
                status_code=400,
                detail=f"Spool #{spool_input.spool_id} not found"
            )
        cost_per_kg = (
            round((spool.purchase_price / spool.total_weight_g) * 1000, 4)
            if spool.total_weight_g > 0 else 0.0
        )
        order_spool = OrderSpool(
            order_id=order.id,
            spool_id=spool_input.spool_id,
            filament_grams=spool_input.filament_grams,
            position=spool_input.position,
            cost_per_kg_snapshot=cost_per_kg,
        )
        db.add(order_spool)

    # Process hardware items
    for hw_input in data.hardware_items:
        if hw_input.is_one_off:
            oh = OrderHardware(
                order_id=order.id,
                hardware_item_id=None,
                quantity=hw_input.quantity,
                unit_cost_snapshot=hw_input.one_off_cost,
                is_one_off=True,
                one_off_name=hw_input.one_off_name,
                one_off_cost=hw_input.one_off_cost,
            )
        else:
            hardware_item = db.query(HardwareItem).filter(
                HardwareItem.id == hw_input.hardware_item_id
            ).first()
            if not hardware_item:
                raise HTTPException(
                    status_code=400,
                    detail=f"Hardware item {hw_input.hardware_item_id} not found"
                )
            oh = OrderHardware(
                order_id=order.id,
                hardware_item_id=hw_input.hardware_item_id,
                quantity=hw_input.quantity,
                unit_cost_snapshot=hardware_item.cost_per_item,
                hardware_name_snapshot=hardware_item.name,
                hardware_brand_snapshot=hardware_item.brand,
            )
        db.add(oh)

        # Note: Hardware stock is NOT decremented on creation
        # It will be decremented when order status changes to "finished"

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to create order for user %s", current_user.id, exc_info=True)
        raise
    return _load_order(db, order.id)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    return _load_order(db, order_id)


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, data: OrderUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    order = (
        db.query(Order)
        .options(
            joinedload(Order.order_hardware),
            joinedload(Order.order_spools),
        )
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Track old status before update
    old_status = order.status
    update_data = data.model_dump(exclude_unset=True)
    hardware_items_update = update_data.pop("hardware_items", None)
    spools_was_set = "spools" in update_data
    spools_update = update_data.pop("spools", None)

    if "project_id" in update_data:
        pid = update_data["project_id"]
        if pid:
            project = db.query(Project).filter(Project.id == pid).first()
            if not project:
                raise HTTPException(status_code=400, detail="Project not found")
            # Re-snapshot when project changes
            order.filament_grams_snapshot = project.filament_grams
            order.print_time_hours_snapshot = project.print_time_hours
        else:
            order.filament_grams_snapshot = None
            order.print_time_hours_snapshot = None
    if "spool_id" in update_data:
        sid = update_data["spool_id"]
        if sid and not db.query(Spool).filter(Spool.id == sid).first():
            raise HTTPException(status_code=400, detail="Spool not found")

    # Apply updates
    for key, value in update_data.items():
        setattr(order, key, value)

    new_status = order.status

    # Handle order spools replacement if provided (Issue #76)
    if spools_was_set and spools_update is not None:
        if spools_update:
            positions = [s["position"] for s in spools_update]
            if len(positions) != len(set(positions)):
                raise HTTPException(status_code=400, detail="Duplicate spool positions are not allowed")
        for old_os in list(order.order_spools):
            db.delete(old_os)
        db.flush()
        for spool_data in spools_update:
            spool = db.query(Spool).filter(Spool.id == spool_data["spool_id"]).first()
            if not spool:
                raise HTTPException(
                    status_code=400,
                    detail=f"Spool #{spool_data['spool_id']} not found"
                )
            cost_per_kg = (
                round((spool.purchase_price / spool.total_weight_g) * 1000, 4)
                if spool.total_weight_g > 0 else 0.0
            )
            new_os = OrderSpool(
                order_id=order.id,
                spool_id=spool_data["spool_id"],
                filament_grams=spool_data["filament_grams"],
                position=spool_data["position"],
                cost_per_kg_snapshot=cost_per_kg,
            )
            db.add(new_os)
        db.flush()

    # Handle hardware replacement if provided
    if hardware_items_update is not None:
        # If order is/was "finished", restore stock for old inventory items before replacing
        if old_status == "finished":
            for oh in order.order_hardware:
                if not oh.is_one_off and oh.hardware_item_id:
                    hardware_item = db.query(HardwareItem).filter(
                        HardwareItem.id == oh.hardware_item_id
                    ).first()
                    if hardware_item:
                        hardware_item.quantity_in_stock += oh.quantity

        # Replace all hardware items
        for oh in list(order.order_hardware):
            db.delete(oh)
        db.flush()

        for hw_input in data.hardware_items:
            if hw_input.is_one_off:
                oh = OrderHardware(
                    order_id=order.id,
                    hardware_item_id=None,
                    quantity=hw_input.quantity,
                    unit_cost_snapshot=hw_input.one_off_cost,
                    is_one_off=True,
                    one_off_name=hw_input.one_off_name,
                    one_off_cost=hw_input.one_off_cost,
                )
            else:
                hardware_item = db.query(HardwareItem).filter(
                    HardwareItem.id == hw_input.hardware_item_id
                ).first()
                if not hardware_item:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Hardware item {hw_input.hardware_item_id} not found"
                    )
                oh = OrderHardware(
                    order_id=order.id,
                    hardware_item_id=hw_input.hardware_item_id,
                    quantity=hw_input.quantity,
                    unit_cost_snapshot=hardware_item.cost_per_item,
                    hardware_name_snapshot=hardware_item.name,
                    hardware_brand_snapshot=hardware_item.brand,
                )
            db.add(oh)
        db.flush()

        # Re-load order_hardware for status change logic below
        db.refresh(order)

    # Handle hardware inventory deduction/restoration based on status change.
    # Deduct when status just changed TO "finished", OR when status stays "finished" but
    # hardware items were replaced (old stock was already restored in the block above).
    needs_deduct = new_status == "finished" and (
        old_status != "finished" or hardware_items_update is not None
    )
    # Restore when status changed FROM "finished" and hardware was NOT already restored above.
    needs_restore = old_status == "finished" and new_status != "finished" and hardware_items_update is None

    if needs_deduct:
        for oh in order.order_hardware:
            if oh.is_one_off:
                continue  # No stock to deduct for one-off items
            hardware_item = db.query(HardwareItem).filter(
                HardwareItem.id == oh.hardware_item_id
            ).first()
            if hardware_item:
                if hardware_item.quantity_in_stock < oh.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient stock for {hardware_item.name}. "
                               f"Available: {hardware_item.quantity_in_stock}, "
                               f"Required: {oh.quantity}"
                    )
                hardware_item.quantity_in_stock -= oh.quantity

    elif needs_restore:
        for oh in order.order_hardware:
            if oh.is_one_off:
                continue
            hardware_item = db.query(HardwareItem).filter(
                HardwareItem.id == oh.hardware_item_id
            ).first()
            if hardware_item:
                hardware_item.quantity_in_stock += oh.quantity

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to update order %s for user %s", order_id, current_user.id, exc_info=True)
        raise

    # Fire order_status_change webhook if status changed
    if old_status != new_status:
        settings_row = db.query(AppSettings).filter(AppSettings.id == 1).first()
        if settings_row and settings_row.webhook_enabled and settings_row.webhook_url:
            import json as _json
            try:
                events = _json.loads(settings_row.webhook_events or "[]")
            except (ValueError, TypeError):
                events = []
            if "order_status_change" in events:
                webhook_url = settings_row.webhook_url
                background_tasks.add_task(
                    send_order_status_change_webhook,
                    webhook_url, order, old_status, new_status
                )

    return _load_order(db, order.id)


@router.delete("/{order_id}", status_code=204)
def delete_order(order_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    order = (
        db.query(Order)
        .options(joinedload(Order.order_hardware))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Restore hardware stock ONLY if order was "finished"
    # (hardware is only deducted when status becomes "finished")
    if order.status == "finished":
        for oh in order.order_hardware:
            if oh.is_one_off:
                continue  # No stock to restore for one-off items
            hardware_item = db.query(HardwareItem).filter(
                HardwareItem.id == oh.hardware_item_id
            ).first()
            if hardware_item:
                hardware_item.quantity_in_stock += oh.quantity

    db.delete(order)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to delete order %s for user %s", order_id, current_user.id, exc_info=True)
        raise


def _compute_order_cost_breakdown(order: Order, settings: AppSettings | None) -> dict:
    filament_cost = 0.0
    if order.order_spools:
        for os in order.order_spools:
            filament_cost += os.filament_grams * ((os.cost_per_kg_snapshot or 0.0) / 1000)
    else:
        filament_grams = order.filament_grams_snapshot
        if filament_grams is None and order.project:
            filament_grams = order.project.filament_grams
        filament_grams = filament_grams or 0.0
        if order.spool and filament_grams > 0:
            spool = order.spool
            if spool.purchase_price and spool.total_weight_g > 0:
                filament_cost = filament_grams * (spool.purchase_price / spool.total_weight_g)
    hardware_cost = sum(oh.unit_cost_snapshot * oh.quantity for oh in order.order_hardware)
    print_time_hours = order.print_time_hours_snapshot
    if print_time_hours is None and order.project:
        print_time_hours = order.project.print_time_hours
    electricity_cost = time_cost = depreciation_cost = 0.0
    if settings and print_time_hours:
        hours = print_time_hours
        electricity_cost = hours * (settings.printer_wattage / 1000) * settings.electricity_rate_kwh
        time_cost = hours * settings.hourly_rate
        depreciation_cost = hours * settings.machine_depreciation_rate
    return {
        "filament_cost": filament_cost, "hardware_cost": hardware_cost,
        "electricity_cost": electricity_cost, "time_cost": time_cost,
        "depreciation_cost": depreciation_cost,
    }


def _calculate_order_cost(order: Order, settings: AppSettings | None) -> float:
    return sum(_compute_order_cost_breakdown(order, settings).values())


@router.get("/{order_id}/profit", response_model=OrderProfitBreakdown)
def get_order_profit(order_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    order = _load_order(db, order_id)
    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    currency = settings.currency_symbol if settings else "$"

    revenue = order.quoted_price or 0.0
    shipping_revenue = order.shipping_charge or 0.0
    total_revenue = revenue + shipping_revenue

    bd = _compute_order_cost_breakdown(order, settings)
    total_cost = sum(bd.values())

    return OrderProfitBreakdown(
        revenue=round(revenue, 2),
        shipping_revenue=round(shipping_revenue, 2),
        filament_cost=round(bd["filament_cost"], 2),
        hardware_cost=round(bd["hardware_cost"], 2),
        electricity_cost=round(bd["electricity_cost"], 2),
        time_cost=round(bd["time_cost"], 2),
        depreciation_cost=round(bd["depreciation_cost"], 2),
        total_cost=round(total_cost, 2),
        profit=round(total_revenue - total_cost, 2),
        currency_symbol=currency,
    )


@router.get("/{order_id}/invoice", response_model=OrderInvoiceResponse)
def get_order_invoice(
    order_id: int,
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user),
):
    """Return invoice data for a single order — used to render a printable receipt."""
    order = (
        db.query(Order)
        .options(
            joinedload(Order.order_hardware),
            joinedload(Order.project),
            joinedload(Order.order_spools).joinedload(OrderSpool.spool).joinedload(Spool.filament_type),
        )
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
    currency = settings.currency_symbol if settings else "$"

    item_name = order.custom_name or (order.project.name if order.project else None)

    filament_lines: list[OrderInvoiceFilamentLine] = []
    for os in order.order_spools:
        if os.spool:
            filament_lines.append(OrderInvoiceFilamentLine(
                color_name=os.spool.color_name,
                filament_type=os.spool.filament_type.name if os.spool.filament_type else "",
                color_hex=os.spool.color_hex,
                grams=os.filament_grams,
            ))

    hardware_lines: list[OrderInvoiceHardwareLine] = []
    for oh in order.order_hardware:
        if oh.is_one_off:
            name = oh.one_off_name or "Item"
            brand = None
            unit_cost = oh.one_off_cost or 0.0
        else:
            name = oh.hardware_name_snapshot or (oh.hardware_item.name if oh.hardware_item else "Item")
            brand = oh.hardware_brand_snapshot or (oh.hardware_item.brand if oh.hardware_item else None)
            unit_cost = oh.unit_cost_snapshot
        hardware_lines.append(OrderInvoiceHardwareLine(
            name=name,
            brand=brand,
            quantity=oh.quantity,
            unit_cost=unit_cost,
        ))

    return OrderInvoiceResponse(
        order_id=order.id,
        customer_name=order.customer_name,
        customer_contact=order.customer_contact,
        customer_location=order.customer_location,
        status=order.status,
        item_name=item_name,
        quoted_price=order.quoted_price,
        shipping_charge=order.shipping_charge,
        due_date=order.due_date,
        created_at=order.created_at,
        filament_lines=filament_lines,
        hardware_lines=hardware_lines,
        currency_symbol=currency,
        notes=order.notes,
    )


@router.post("/check-notifications")
async def check_notifications(db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    """Manual trigger for Discord order notifications (for testing)."""
    count = await check_and_notify_overdue_orders(db)
    return {"notifications_sent": count}


@router.post("/{order_id}/create-print-job")
def create_print_job_from_order(
    order_id: int,
    force: bool = False,
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user)
):
    """Create a print job from an order and deduct filament.

    Supports multi-color orders: if the order has order_spools entries, creates
    a multi-color PrintJob using PrintJobSpool records (Issue #77).
    Falls back to legacy single-spool behavior for orders with only spool_id.
    """
    order = _load_order(db, order_id)

    if not order.project_id:
        raise HTTPException(
            status_code=400,
            detail="Order must have a project to create print job"
        )

    project = order.project
    if not project:
        raise HTTPException(status_code=400, detail="Project not found")

    job_name = f"{order.custom_name or project.name} - Order #{order.id}"

    # Multi-color path: order has order_spools entries (Issue #77)
    if order.order_spools:
        spool_usages = [(os.spool_id, os.filament_grams) for os in order.order_spools]

        # Validate inventory (unless force=True)
        if not force:
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

        pj_settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
        prevent = pj_settings.enable_spool_negative_prevention if pj_settings else True

        print_job = PrintJob(
            order_id=order.id,
            name=job_name,
            description=f"Print job created from order #{order.id}",
            print_time_minutes=int((project.print_time_hours or 0.0) * 60),
            status="completed",
            was_for_customer=True,
            customer_name=order.customer_name,
            quoted_price=order.quoted_price,
            notes=order.notes,
        )
        db.add(print_job)
        db.flush()

        for os in order.order_spools:
            pjs = PrintJobSpool(
                print_job_id=print_job.id,
                spool_id=os.spool_id,
                filament_used_g=os.filament_grams,
                position=os.position,
            )
            db.add(pjs)

            spool = db.query(Spool).filter(Spool.id == os.spool_id).first()
            if spool and os.filament_grams > 0:
                _deduct_spool(spool, os.filament_grams, prevent)

    elif order.spool_id:
        # Legacy single-spool path
        filament_grams = project.filament_grams or 0.0

        # Validate inventory (unless force=True)
        if filament_grams > 0 and not force:
            validation = validate_spool_inventory(
                db,
                [(order.spool_id, filament_grams)]
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

        pj_settings = db.query(AppSettings).filter(AppSettings.id == 1).first()
        prevent = pj_settings.enable_spool_negative_prevention if pj_settings else True

        print_job = PrintJob(
            spool_id=order.spool_id,
            order_id=order.id,
            name=job_name,
            description=f"Print job created from order #{order.id}",
            filament_used_g=filament_grams,
            print_time_minutes=int((project.print_time_hours or 0.0) * 60),
            status="completed",
            was_for_customer=True,
            customer_name=order.customer_name,
            quoted_price=order.quoted_price,
            notes=order.notes,
        )
        db.add(print_job)
        db.flush()

        spool = db.query(Spool).filter(Spool.id == order.spool_id).first()
        if spool and print_job.filament_used_g and print_job.filament_used_g > 0:
            _deduct_spool(spool, print_job.filament_used_g, prevent)

    else:
        raise HTTPException(
            status_code=400,
            detail="Order must have spools or spool_id to create print job"
        )

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to create print job from order %s", order_id, exc_info=True)
        raise
    db.refresh(print_job)

    return {"message": "Print job created successfully", "print_job_id": print_job.id}
