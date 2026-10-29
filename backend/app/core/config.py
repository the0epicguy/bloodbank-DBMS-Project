"""
Application configuration loaded from environment variables / .env file.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "bloodbank_db"

    # Application
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_DEBUG: bool = False

    # App metadata
    APP_TITLE: str = "Blood Bank Management System"
    APP_VERSION: str = "1.0.0"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    # ── Business Rules ────────────────────────────────────────────────
    MIN_DONOR_AGE: int = 18
    MAX_DONOR_AGE: int = 65
    DONATION_GAP_DAYS: int = 90
    EXPIRY_WARNING_DAYS: int = 7
    CRITICAL_STOCK_THRESHOLD: int = 5

    # ── Authentication (Person 4) ─────────────────────────────────────
    JWT_SECRET: str = "change-me-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8 hours
    ALLOW_DEMO_LOGIN: bool = True

    # Demo seeding
    SEED_DEMO_USERS: bool = False
    DEMO_PASSWORD: str = "demo1234"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
