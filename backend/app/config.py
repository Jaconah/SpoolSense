from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./data/spoolsense.db"

    # Secrets — auto-generated on first run and stored in the DB.
    # Only set these manually if you need token portability across multiple instances.
    JWT_SECRET_KEY: str = ""
    SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Production frontend URL (required in production for CORS)
    FRONTEND_URL: str = ""
    ENVIRONMENT: str = "production"  # default; set to "development" for local dev

    # Optional — webhook for error/alert notifications
    ERROR_WEBHOOK_URL: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# Resolve the database path relative to backend/
BASE_DIR = Path(__file__).resolve().parent.parent

if settings.DATABASE_URL.startswith("sqlite:///./"):
    relative_path = settings.DATABASE_URL.replace("sqlite:///./", "")
    db_path = BASE_DIR / relative_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_path}"
else:
    DATABASE_URL = settings.DATABASE_URL
