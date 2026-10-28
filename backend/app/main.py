from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, SessionLocal
from app.core.seeder import init_tables, seed_demo_data
from app.routers import auth, issues, reports

@asynccontextmanager
async def lifespan(app: FastAPI):
    if "sqlite" in settings.database_url:
        await init_tables(engine)
    if settings.seed_demo_users:
        async with SessionLocal() as db:
            await seed_demo_data(db)
    yield

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Person 4: authentication, issue allocation, audit log and reports",
    lifespan=lifespan
)
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(issues.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)

@app.get("/health")
async def health():
    return {"status": "ok"}
