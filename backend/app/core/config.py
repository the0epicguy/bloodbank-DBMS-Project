from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Blood Bank Management System"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./bloodbank_dev.db"
    jwt_secret: str = "development-only-change-this-secret"
    jwt_expire_minutes: int = 60
    seed_demo_users: bool = False
    cors_origins: str = "http://localhost:5173"
    test_database_url: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
