"""
Sync SQLAlchemy engine, session factory, and declarative Base.
All repos use Session; get_db() yields one per request and auto-commits.
Includes automatic fallback to local SQLite when MySQL is not running or credentials fail.
"""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

Base = declarative_base()


def _build_engine():
    try:
        eng = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=settings.APP_DEBUG,
        )
        # Test connection immediately
        with eng.connect() as conn:
            pass
        logger.info(f"[Database] Connected to MySQL database '{settings.DB_NAME}' successfully.")
        return eng
    except Exception as e:
        logger.warning(
            f"[Database] Could not connect to MySQL at {settings.DB_HOST}:{settings.DB_PORT} ({e}). "
            "Falling back to local SQLite database ('sqlite:///./bloodbank_local.db') "
            "so the application runs and communicates immediately."
        )
        fallback_engine = create_engine(
            "sqlite:///./bloodbank_local.db",
            connect_args={"check_same_thread": False},
            echo=settings.APP_DEBUG,
        )
        return fallback_engine


engine = _build_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency: yields a DB session, commits on success,
    rolls back on exception, and always closes the session.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

