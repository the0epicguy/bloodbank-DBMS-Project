"""
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

# Create the FastAPI application
app = FastAPI(
    title="Blood Bank Management System",
    description="API for managing blood donations, inventory, and requests",
    version="1.0.0",
)

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

# Person 4: Auth, Issues and Reports
from app.routers import auth, issues, reports
app.include_router(auth.router)
app.include_router(issues.router)
app.include_router(issues.fulfil_router)
app.include_router(reports.router)
