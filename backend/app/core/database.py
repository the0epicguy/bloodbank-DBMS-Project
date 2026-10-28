"""
core/database.py
================
SQLAlchemy 2.0 async engine, session factory, and Base declarative model.
All models import `Base` from here; all repos use `AsyncSession`.

Dependency:
    async def get_db() -> AsyncGenerator[AsyncSession, None]
    — inject with FastAPI Depends() in every router.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ---------------------------------------------------------------------------
# SQLAlchemy async engine
# ---------------------------------------------------------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,          # Log SQL statements in debug mode
    pool_pre_ping=True,           # Verify connection health before using from pool
    pool_recycle=1800,            # Recycle connections every 30 min (avoids MySQL 8h timeout)
    pool_size=10,
    max_overflow=20,
)

# Session factory (does NOT auto-commit or auto-flush by default)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,       # Keep loaded attributes accessible after commit
)


# ---------------------------------------------------------------------------
# Declarative Base — all ORM models inherit from this
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency: inject a DB session per request
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async database session.  The session is automatically closed
    and the connection is returned to the pool when the request finishes,
    whether or not an exception was raised.

    Usage in routers:
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
