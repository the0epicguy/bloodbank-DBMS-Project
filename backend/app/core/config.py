"""
core/config.py
==============
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
    """
    return Settings()


# Module-level convenience — import `settings` anywhere
settings: Settings = get_settings()
