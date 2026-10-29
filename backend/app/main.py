"""
app/main.py
FastAPI application factory — the entry point for `uvicorn app.main:app`.
Person 2 is responsible for the app scaffold and router registration.
FastAPI application entry point.

This file:
    1. Creates the FastAPI app instance
    2. Configures CORS middleware
    3. Registers all routers
    4. Provides a health-check endpoint

Run with:
    uvicorn app.main:app --reload
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
from app.core.config import settings
from app.routers import hospitals, recipients, requests

# Create the FastAPI application
app = FastAPI(
    title="Blood Bank Management System",
    description="API for managing blood donations, inventory, and requests",
    version="1.0.0",
)

app.include_router(hospitals.router)
app.include_router(recipients.router)
app.include_router(requests.router)


# Configure CORS — allows the React frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],    # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Blood Bank API is running"}


@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": settings.DB_HOST,
        "debug": settings.APP_DEBUG,
    }


# ---- Router Registration ----
# Routers are imported and included here.
# As each person adds their routers, they add an include line below.

# Person 1: Donors and Donations
from app.routers import donors, donations
app.include_router(donors.router)
app.include_router(donations.router)

# Person 2: Banks and Units (uncomment when ready)
# from app.routers import banks, units
# app.include_router(banks.router)
# app.include_router(units.router)

# Person 3: Hospitals, Recipients, Requests (uncomment when ready)
# from app.routers import hospitals, recipients, requests
# app.include_router(hospitals.router)
# app.include_router(recipients.router)
# app.include_router(requests.router)

# Person 4: Issues and Reports (uncomment when ready)
# from app.routers import issues, reports
# app.include_router(issues.router)
# app.include_router(reports.router)
