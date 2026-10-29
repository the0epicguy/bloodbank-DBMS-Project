"""
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

    # Authentication (Person 4)
    JWT_SECRET: str = "change-me-in-production-please-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8 hours
    ALLOW_DEMO_LOGIN: bool = True  # 1-click quick-login buttons (turn off in production)

    # Reports (Person 4)
    CRITICAL_STOCK_THRESHOLD: int = 5  # units per blood group below which stock is "critical"

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


# Convenient reference
settings = get_settings()
