import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select, func
from sqlalchemy.orm import Session, joinedload

from app.middleware.tenant import get_current_user, get_tenant_db
from app.middleware.tenant import SimpleUser as User
from app.models.hardware import HardwareItem
from app.models.project import Project, ProjectFilament, ProjectHardware
from app.models.product_on_hand import ProductOnHand
from app.schemas.common import PaginatedResponse
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=PaginatedResponse[ProjectResponse])
def list_projects(
    include_inactive: bool = False,
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_tenant_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Project)
    if not include_inactive:
        query = query.filter(Project.is_active == True)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(
            Project.name.ilike(term),
            Project.description.ilike(term),
            Project.notes.ilike(term),
        ))
    total = query.count()
    items = (
        query
        .options(
            joinedload(Project.hardware).joinedload(ProjectHardware.hardware_item),
            joinedload(Project.project_filaments),
        )
        .order_by(Project.name)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return PaginatedResponse(items=items, total=total, page=page, per_page=per_page)



@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    hw_list = data.hardware
    project_data = data.model_dump(exclude={"hardware"})
    project = Project(**project_data)
    db.add(project)
    db.flush()

    for hw in hw_list:
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
        logger.error("Failed to create project for user %s", current_user.id, exc_info=True)
        raise
    db.refresh(project)
    # Reload with joins
    return (
        db.query(Project)
        .options(
            joinedload(Project.hardware).joinedload(ProjectHardware.hardware_item),
            joinedload(Project.project_filaments),
        )
        .filter(Project.id == project.id)
        .first()
    )


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    project = (
        db.query(Project)
        .options(
            joinedload(Project.hardware).joinedload(ProjectHardware.hardware_item),
            joinedload(Project.project_filaments),
        )
        .filter(Project.id == project_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = data.model_dump(exclude_unset=True)
    hw_list = update_data.pop("hardware", None)

    for key, value in update_data.items():
        setattr(project, key, value)

    if hw_list is not None:
        # Validate ALL new hardware items first before deleting anything
        for hw in hw_list:
            if not db.query(HardwareItem).filter(HardwareItem.id == hw["hardware_item_id"]).first():
                raise HTTPException(
                    status_code=400, detail=f"Hardware item {hw['hardware_item_id']} not found"
                )
        # All valid — replace hardware associations
        db.query(ProjectHardware).filter(ProjectHardware.project_id == project_id).delete()
        for hw in hw_list:
            ph = ProjectHardware(
                project_id=project_id,
                hardware_item_id=hw["hardware_item_id"],
                quantity=hw.get("quantity", 1),
            )
            db.add(ph)

    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to update project %s for user %s", project_id, current_user.id, exc_info=True)
        raise
    db.refresh(project)
    return (
        db.query(Project)
        .options(
            joinedload(Project.hardware).joinedload(ProjectHardware.hardware_item),
            joinedload(Project.project_filaments),
        )
        .filter(Project.id == project.id)
        .first()
    )


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_tenant_db), current_user: User = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if any products on hand reference this project
    products_count = db.scalar(
        select(func.count(ProductOnHand.id)).where(ProductOnHand.project_id == project_id)
    )

    if products_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete project - {products_count} product(s) on hand still exist"
        )

    db.delete(project)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.error("Failed to delete project %s for user %s", project_id, current_user.id, exc_info=True)
        raise
