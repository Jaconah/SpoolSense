from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for monitoring and deployment verification.

    Returns 200 OK if the service is healthy, 503 if the database is unreachable.
    Suitable as an uptime monitor target (UptimeRobot, Pingdom, etc.).
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=503, content={"status": "unhealthy"})

    return {"status": "healthy"}
