"""
app/main.py
===========
FastAPI application factory — the entry point for `uvicorn app.main:app`.
Person 2 is responsible for the app scaffold and router registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.routers import banks, inventory

# -----------------------------------------------------------------------
# Person 3 & 4 routers — uncomment as they are implemented:
# from app.routers import donors, donations     # Person 1
# from app.routers import hospitals, recipients, requests  # Person 3
# from app.routers import issues, reports, auth            # Person 4
# -----------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description=(
        "Blood Bank Management System REST API. "
        "Built with FastAPI, SQLAlchemy 2.0 (async), MySQL 8.0."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# -----------------------------------------------------------------------
# CORS — allow the Vite dev server (port 5173) during development
# -----------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------
# Global exception handlers
# -----------------------------------------------------------------------
register_exception_handlers(app)

# -----------------------------------------------------------------------
# Router registration
# -----------------------------------------------------------------------
app.include_router(banks.router)
app.include_router(inventory.router)


# -----------------------------------------------------------------------
# Root health-check endpoint
# -----------------------------------------------------------------------
@app.get("/", tags=["health"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_TITLE,
        "version": settings.APP_VERSION,
    }
