"""Product on Hand API endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload
from typing import List

from ..middleware.tenant import get_current_user, get_tenant_db
from ..middleware.tenant import SimpleUser as User
from ..models.product_on_hand import ProductOnHand
from ..models.print_job import PrintJob, PrintJobSpool
from ..models.project import Project, ProjectHardware
from ..models.order import Order, OrderHardware
from ..schemas.product_on_hand import (
    ConvertToOrderRequest,
    ProductOnHandCreate,
    ProductOnHandUpdate,
    ProductOnHandResponse,
    ProductOnHandStats
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products-on-hand", tags=["products-on-hand"])


@router.post("", response_model=ProductOnHandResponse)
async def create_product_on_hand(
    data: ProductOnHandCreate,
    db: Session = Depends(get_tenant_db),
    user: User = Depends(get_current_user),
):
    """Create a new Product on Hand from a completed Print Job."""
    # Validate print job exists and is completed
    print_job = db.get(PrintJob, data.print_job_id)
    if not print_job:
        raise HTTPException(status_code=404, detail="Print job not found")
    if print_job.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Only completed print jobs can become products on hand"
        )

    # Validate project exists and check hardware requirements (if project provided)
    project = None
    has_hardware = False
    if data.project_id:
        project = db.query(Project).options(
            joinedload(Project.hardware)
        ).filter(Project.id == data.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        has_hardware = project.hardware and len(project.hardware) > 0

    # Validation: If status is "completed", location is required
    if data.status == "completed" and not data.location:
        raise HTTPException(
            status_code=400,
            detail="Location is required when status is completed"
        )

    # If project has hardware and status is "printed", location should be empty
    # If project has no hardware OR no project, status should be "completed" and location required
    if has_hardware:
        if data.status == "completed" and not data.location:
            raise HTTPException(
                status_code=400,
                detail="Location is required when marking as completed"
            )
    else:
        # No hardware or custom product = ready immediately
        if data.status != "completed":
            raise HTTPException(
                status_code=400,
                detail="Products without hardware should be marked as completed"
            )
        if not data.location:
            raise HTTPException(
                status_code=400,
                detail="Location is required for products without hardware"
            )

    # Warning if print job already linked to order (but allow it)
    if print_job.order_id:
        pass  # Log this if needed

    # Create product
    product = ProductOnHand(**data.model_dump())
    db.add(product)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to create product on hand for user %s", user.id, exc_info=True)
        raise
    db.refresh(product)

    return _serialize_product(db, product)


@router.get("", response_model=List[ProductOnHandResponse])
async def list_products_on_hand(
    project_id: int | None = None,
    db: Session = Depends(get_tenant_db),
    user: User = Depends(get_current_user),
):
    """List all Products on Hand, optionally filtered by project."""
    query = select(ProductOnHand).options(
        joinedload(ProductOnHand.project),
        joinedload(ProductOnHand.print_job).joinedload(PrintJob.spool),
    )

    if project_id:
        query = query.where(ProductOnHand.project_id == project_id)

    query = query.order_by(ProductOnHand.created_at.desc())
    products = db.scalars(query).unique().all()

    return [_serialize_product(db, p) for p in products]


@router.get("/stats", response_model=ProductOnHandStats)
async def get_stats(
    db: Session = Depends(get_tenant_db),
    user: User = Depends(get_current_user),
):
    """Get Product on Hand statistics (count, value, potential profit)."""
    products = db.scalars(select(ProductOnHand)).all()

    total_value = 0.0
    total_profit = 0.0

    logger = logging.getLogger(__name__)
    for product in products:
        try:
            project = db.get(Project, product.project_id) if product.project_id else None
            if project and project.sell_price:
                total_value += project.sell_price

            total_cost = _calculate_product_cost(db, product)
            if project and project.sell_price:
                total_profit += (project.sell_price - total_cost)
        except Exception:
            logger.warning("Failed to calculate stats for product %s", product.id, exc_info=True)

    return ProductOnHandStats(
        total_count=len(products),
        total_value=total_value,
        total_potential_profit=total_profit,
    )


@router.get("/{id}", response_model=ProductOnHandResponse)
async def get_product_on_hand(
    id: int,
    db: Session = Depends(get_tenant_db),
    user: User = Depends(get_current_user),
):
    """Get a single Product on Hand by ID."""
    product = db.get(ProductOnHand, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _serialize_product(db, product)


@router.put("/{id}", response_model=ProductOnHandResponse)
async def update_product_on_hand(
    id: int,
    data: ProductOnHandUpdate,
    db: Session = Depends(get_tenant_db),
    user: User = Depends(get_current_user),
):
    """Update Product on Hand - deducts hardware when marking as completed."""
    product = db.get(ProductOnHand, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Track if we're changing status from printed to completed
    was_printed = product.status == "printed"
    will_be_completed = data.status == "completed" if data.status else product.status == "completed"

    # If marking as completed for the first time, deduct hardware inventory
    if was_printed and will_be_completed and product.project_id:
        project = db.query(Project).options(
            joinedload(Project.hardware).joinedload(ProjectHardware.hardware_item)
        ).filter(Project.id == product.project_id).first()

        if project and project.hardware:
            for ph in project.hardware:
                if ph.hardware_item.quantity_in_stock < ph.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient stock for {ph.hardware_item.name}. "
                               f"Available: {ph.hardware_item.quantity_in_stock}, "
                               f"Required: {ph.quantity}"
                    )
            for ph in project.hardware:
                # Deduct hardware from inventory
                ph.hardware_item.quantity_in_stock -= ph.quantity

    # Update fields
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to update product on hand %s for user %s", id, user.id, exc_info=True)
        raise
    db.refresh(product)
    return _serialize_product(db, product)


@router.delete("/{id}", status_code=204)
async def delete_product_on_hand(
    id: int,
    db: Session = Depends(get_tenant_db),
    user: User = Depends(get_current_user),
):
    """Delete a Product on Hand."""
    product = db.get(ProductOnHand, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to delete product on hand %s for user %s", id, user.id, exc_info=True)
        raise


@router.post("/{id}/convert-to-order", response_model=dict)
async def convert_to_order(
    id: int,
    order_data: ConvertToOrderRequest,
    db: Session = Depends(get_tenant_db),
    user: User = Depends(get_current_user),
):
    """
    Convert a Product on Hand to an Order.

    Deletes the product and creates an order with status "sold".
    If quoted_price is 0, treats as "gifted".
    Hardware stock is decremented since order status is immediately "sold".
    """
    product = db.get(ProductOnHand, id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Load print job early for idempotency check and to avoid lazy-load issues
    print_job = db.get(PrintJob, product.print_job_id)
    if not print_job:
        raise HTTPException(status_code=400, detail="Print job not found")
    if print_job.order_id is not None:
        raise HTTPException(status_code=409, detail="This product has already been converted to an order")

    conversion_note = f"Converted from Product on Hand #{product.id}. Original location: {product.location}"
    notes = f"{conversion_note}. {order_data.notes}" if order_data.notes else conversion_note

    # Create order from product
    order = Order(
        project_id=product.project_id,
        spool_id=print_job.spool_id,
        customer_name=order_data.customer_name,
        customer_contact=order_data.customer_contact,
        customer_location=order_data.customer_location,
        quoted_price=order_data.quoted_price,
        status="sold",  # Immediately mark as sold
        notes=notes,
    )

    # Copy hardware from project to order (snapshot costs).
    # Only deduct stock if the product was NOT already "completed" — when a product
    # transitions printed→completed, hardware is deducted in update_product_on_hand.
    # Deducting again here would double-count the same items.
    project = db.get(Project, product.project_id)
    if project and project.hardware:
        # Validate stock only when we're about to deduct (product not yet "completed")
        if product.status != "completed":
            for ph in project.hardware:
                if ph.hardware_item.quantity_in_stock < ph.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient stock for {ph.hardware_item.name}. "
                               f"Available: {ph.hardware_item.quantity_in_stock}, "
                               f"Required: {ph.quantity}"
                    )
        for ph in project.hardware:
            oh = OrderHardware(
                order=order,
                hardware_item_id=ph.hardware_item_id,
                quantity=ph.quantity,
                unit_cost_snapshot=ph.hardware_item.cost_per_item,
            )
            db.add(oh)

            # Only deduct stock if hardware hasn't been deducted already
            if product.status != "completed":
                ph.hardware_item.quantity_in_stock -= ph.quantity

    db.add(order)
    db.flush()  # Assign order.id before linking the print job

    # Link the print job to the order
    print_job.order_id = order.id

    db.delete(product)  # Remove from Product on Hand
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to convert product on hand %s to order for user %s", id, user.id, exc_info=True)
        raise
    db.refresh(order)

    return {
        "order_id": order.id,
        "message": "Product converted to order successfully"
    }


# Helper functions

def _calculate_product_cost(db: Session, product: ProductOnHand) -> float:
    """Calculate total cost: filament + hardware."""
    filament_cost = 0.0
    hardware_cost = 0.0

    # Filament cost from print job — prefer multi-color spools, fall back to legacy single spool
    print_job = db.query(PrintJob).options(
        joinedload(PrintJob.print_job_spools).joinedload(PrintJobSpool.spool),
        joinedload(PrintJob.spool)
    ).filter(PrintJob.id == product.print_job_id).first()

    if print_job:
        if print_job.print_job_spools:
            for pjs in print_job.print_job_spools:
                if pjs.spool and pjs.spool.total_weight_g > 0:
                    filament_cost += pjs.filament_used_g * (pjs.spool.purchase_price / pjs.spool.total_weight_g)
        elif print_job.spool and print_job.filament_used_g:
            spool = print_job.spool
            if spool.total_weight_g > 0:
                filament_cost = print_job.filament_used_g * (spool.purchase_price / spool.total_weight_g)

    # Hardware cost from project
    project = db.query(Project).options(
        joinedload(Project.hardware).joinedload(ProjectHardware.hardware_item)
    ).filter(Project.id == product.project_id).first()

    if project and project.hardware:
        for ph in project.hardware:
            hardware_cost += ph.hardware_item.cost_per_item * ph.quantity

    return round(filament_cost + hardware_cost, 2)


def _serialize_product(db: Session, product: ProductOnHand) -> ProductOnHandResponse:
    """Serialize product with all computed fields."""
    # Load project with hardware relationships (if exists)
    project = None
    if product.project_id:
        project = db.query(Project).options(
            joinedload(Project.hardware).joinedload(ProjectHardware.hardware_item)
        ).filter(Project.id == product.project_id).first()

    # Load print job with spool(s)
    print_job = db.query(PrintJob).options(
        joinedload(PrintJob.spool),
        joinedload(PrintJob.print_job_spools).joinedload(PrintJobSpool.spool),
    ).filter(PrintJob.id == product.print_job_id).first()

    filament_cost = 0.0
    hardware_cost = 0.0
    color = "Unknown"
    hardware_items = []

    if print_job:
        if print_job.print_job_spools:
            for pjs in print_job.print_job_spools:
                if pjs.spool and pjs.spool.total_weight_g > 0:
                    filament_cost += pjs.filament_used_g * (pjs.spool.purchase_price / pjs.spool.total_weight_g)
            first = print_job.print_job_spools[0]
            color = (first.spool.color_name if first.spool else None) or "Unknown"
        elif print_job.spool:
            spool = print_job.spool
            if spool.total_weight_g > 0 and print_job.filament_used_g:
                filament_cost = print_job.filament_used_g * (spool.purchase_price / spool.total_weight_g)
            color = spool.color_name or "Unknown"

    if project and project.hardware:
        for ph in project.hardware:
            hardware_cost += ph.hardware_item.cost_per_item * ph.quantity
            hardware_items.append({
                "id": ph.hardware_item.id,
                "name": ph.hardware_item.name,
                "quantity": ph.quantity,
                "cost_per_item": ph.hardware_item.cost_per_item,
            })

    total_cost = filament_cost + hardware_cost
    sell_price = project.sell_price if project else None
    potential_profit = (sell_price - total_cost) if sell_price is not None else None

    return ProductOnHandResponse(
        id=product.id,
        project_id=product.project_id,
        print_job_id=product.print_job_id,
        name=product.name,
        status=product.status,
        location=product.location,
        notes=product.notes,
        created_at=product.created_at,
        project_name=project.name if project else None,
        color=color,
        filament_cost=round(filament_cost, 2),
        hardware_cost=round(hardware_cost, 2),
        total_cost=round(total_cost, 2),
        sell_price=sell_price,
        potential_profit=round(potential_profit, 2) if potential_profit is not None else None,
        hardware_items=hardware_items,
    )
