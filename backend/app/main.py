import logging
import logging.handlers
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.database import engine, SessionLocal
from app.models.base import Base
from app.models.settings import AppSettings  # noqa: F401
from app.models.filament import FilamentType, Manufacturer, Spool  # noqa: F401
from app.models.print_job import PrintJob  # noqa: F401
from app.models.hardware import HardwareItem  # noqa: F401
from app.models.project import Project, ProjectHardware  # noqa: F401
from app.models.order import Order, OrderHardware  # noqa: F401
from app.services.scheduler import start_scheduler, shutdown_scheduler
from app.services.error_reporter import install_error_handler
from app.config import settings


def _setup_file_logging() -> None:
    log_dir = Path(__file__).resolve().parent.parent / "data" / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        import sys
        print(
            f"[WARNING] Cannot create log directory {log_dir} (permission denied). "
            "File logging disabled; logging to stdout only.",
            file=sys.stderr,
        )
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=log_dir / "app.log",
        when="midnight",
        backupCount=2,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    _noisy = frozenset({"sqlalchemy.engine", "uvicorn.access", "apscheduler"})

    class _FileFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.name not in _noisy

    file_handler.addFilter(_FileFilter())

    root = logging.getLogger()
    root.addHandler(file_handler)


_setup_file_logging()

_access_logger = logging.getLogger("app.access")

# Default password for first-run ("changeme") — user should change this immediately
_DEFAULT_PASSWORD_HASH = "$2b$12$2eOdcHAumeU4XnIhUClmgelK2b4LOmf3yOknQEOp7Kd4QxLnc8d7u"


@asynccontextmanager
async def lifespan(app: FastAPI):
    import secrets as _secrets

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Ensure singleton AppSettings row exists and secrets are generated
    db = SessionLocal()
    try:
        row = db.query(AppSettings).filter_by(id=1).first()
        if not row:
            row = AppSettings(id=1, password_hash=_DEFAULT_PASSWORD_HASH)
            db.add(row)
            db.flush()
            print("✓ AppSettings initialized with default password 'changeme' — change it via Profile → Change Password")

        # Auto-generate JWT and app secrets on first run; persist so tokens survive restarts
        changed = False
        if not row.jwt_secret:
            row.jwt_secret = _secrets.token_hex(32)
            changed = True
        if not row.app_secret:
            row.app_secret = _secrets.token_hex(32)
            changed = True
        if not row.password_hash:
            row.password_hash = _DEFAULT_PASSWORD_HASH
            changed = True
            print("✓ Set default password 'changeme' — change it via Profile → Change Password")
        if changed:
            db.commit()

        # Load persisted secrets into settings so JWT signing is consistent across restarts.
        # Values from .env override the DB (useful for multi-instance deployments).
        if not settings.JWT_SECRET_KEY:
            settings.JWT_SECRET_KEY = row.jwt_secret
        if not settings.SECRET_KEY:
            settings.SECRET_KEY = row.app_secret

    except Exception as e:
        print(f"Warning: Could not initialize AppSettings: {e}")
    finally:
        db.close()

    install_error_handler()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="SpoolSense",
    description="Track filament inventory, log print jobs, and estimate costs",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting
from app.rate_limit import limiter, get_real_ip
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def access_log_middleware(request: Request, call_next):
    response = await call_next(request)
    real_ip = get_real_ip(request)
    _access_logger.info(
        f'{real_ip} "{request.method} {request.url.path}" {response.status_code}'
    )
    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "style-src-elem 'self'; "
        "style-src-attr 'none'; "
        "img-src 'self' data: https://api.qrserver.com; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self';"
    )
    if settings.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# CORS
# If FRONTEND_URL is set, restrict to that origin (reverse proxy / custom domain setup).
# Otherwise allow all origins — covers direct IP:port access and local dev.
if settings.FRONTEND_URL:
    cors_origins = [settings.FRONTEND_URL, "http://localhost:5173"]
    cors_allow_all = False
else:
    cors_origins = ["*"]
    cors_allow_all = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=not cors_allow_all,  # credentials + wildcard origin is disallowed by spec
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Routers
from app.routers import (  # noqa: E402
    auth,
    export,
    health,
    filament_types,
    manufacturers,
    spools,
    print_jobs,
    settings as settings_router,
    cost_estimator,
    dashboard,
    hardware,
    projects,
    orders,
    product_on_hand,
)

app.include_router(auth.router)
app.include_router(health.router, prefix="/api/v1")
app.include_router(filament_types.router, prefix="/api/v1")
app.include_router(manufacturers.router, prefix="/api/v1")
app.include_router(spools.router, prefix="/api/v1")
app.include_router(print_jobs.router, prefix="/api/v1")
app.include_router(settings_router.router, prefix="/api/v1")
app.include_router(cost_estimator.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(hardware.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(product_on_hand.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")


# Serve static frontend (production)
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve the SPA for any non-API route."""
        resolved_static = STATIC_DIR.resolve()
        file_path = (STATIC_DIR / full_path).resolve()
        try:
            file_path.relative_to(resolved_static)
        except ValueError:
            return FileResponse(resolved_static / "index.html")

        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(STATIC_DIR / "index.html")
