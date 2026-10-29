"""
core/config.py
Centralised application settings loaded from the .env file (or environment).
All teammates import from here — never read os.environ directly.

Usage:
    from app.core.config import settings
    print(settings.DATABASE_URL)
"""

from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------ MySQL -------------------------------------------------------
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DB: str = "bloodbank_db"

    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URL(self) -> str:  # noqa: N802
        """Async SQLAlchemy URL (aiomysql driver)."""
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def SYNC_DATABASE_URL(self) -> str:  # noqa: N802
        """Sync SQLAlchemy URL (PyMySQL driver) — used only by Alembic migrations."""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"
        )

    # ------ Security ----------------------------------------------------
    SECRET_KEY: str = "changeme_use_openssl_rand_hex_32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # ------ App ---------------------------------------------------------
    APP_TITLE: str = "Blood Bank Management System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ------ Domain constants (mirrors core/enums.py) -------------------
    MIN_DONATION_INTERVAL_DAYS: int = 90
    DONOR_MIN_AGE: int = 18
    DONOR_MAX_AGE: int = 65

    # Low-stock alert threshold per blood group per bank
    LOW_STOCK_THRESHOLD: int = 5

    # Upcoming expiry warning window (days)
    EXPIRY_WARNING_DAYS: int = 7


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached singleton Settings object.
    Use this in FastAPI Depends() or at module-level imports.
Application configuration loaded from environment variables.

Uses pydantic-settings to validate and parse the .env file.
All settings are available as attributes of the `settings` object.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings.
    Values are read from environment variables or .env file.
    """

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "bloodbank123"
    DB_NAME: str = "bloodbank"

    # Application
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = True

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Business Rules (configurable constants)
    MIN_DONOR_AGE: int = 18
    MAX_DONOR_AGE: int = 65
    DONATION_GAP_DAYS: int = 90  # minimum days between donations

    @property
    def DATABASE_URL(self) -> str:
        """Build the MySQL connection string for SQLAlchemy."""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    The @lru_cache ensures settings are only loaded once.
    """
    return Settings()


# Module-level convenience — import `settings` anywhere
settings: Settings = get_settings()
