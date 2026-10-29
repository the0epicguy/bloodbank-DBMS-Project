"""
app/main.py  —  Blood Bank Management System
=============================================
Unified entry point — registers all 4 team members' routers.

Person 1 (Om):     /donors, /donations
Person 2 (Advait): /api/v1/banks, /api/v1/inventory
Person 3 (Bhoomi): /hospitals, /recipients, /requests
Person 4:          /auth, /issues, /reports
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.routers import (
    # P1
    donors, donations,
    # P2
    banks, inventory,
    # P3
    hospitals, recipients, requests,
    # P4
    auth, issues, reports,
)

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Blood Bank Management System — 4-person DBMS project.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ───────────────────────────────────────────────────────
register_exception_handlers(app)

# ── Person 1: Donors & Donations ─────────────────────────────────────────────
app.include_router(donors.router)
app.include_router(donations.router)

# ── Person 2: Blood Banks & Inventory ────────────────────────────────────────
app.include_router(banks.router)
app.include_router(inventory.router)

# ── Person 3: Hospitals, Recipients & Requests ───────────────────────────────
app.include_router(hospitals.router)
app.include_router(recipients.router)
app.include_router(requests.router)

# ── Person 4: Auth, Issues & Reports ────────────────────────────────────────
app.include_router(auth.router)
app.include_router(issues.router)
app.include_router(reports.router)


# ── Startup event ────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    from app.core.database import engine, Base
    from app.core.db_init import init_database
    init_database(engine, Base)


# ── Health ───────────────────────────────────────────────────────────────────
@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok", "app": settings.APP_TITLE, "version": settings.APP_VERSION}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

