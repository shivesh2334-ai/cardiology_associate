"""
AC Agent — Main Application Entry Point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import init_db
from routers import auth, patients, briefings, notes

# Logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    if settings.ENVIRONMENT == "development":
        await init_db()
        logger.info("Database tables verified / created")
    yield
    logger.info("Shutting down AC Agent API")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="""
## Associate Consultant AI Agent — MVP API

ICU Family Briefing Engine and Clinical Note Generator for Indian hospitals.

### Key Capabilities
- **Family Briefing Generation**: AI-powered plain-language family briefing documents
- **Clinical Note Generation**: SOAP notes for all encounter types
- **Discharge Summary**: Auto-generated from full admission record
- **Human-in-the-Loop**: All AI output requires Associate approval before filing

### Authentication
All endpoints require Bearer token. Obtain via `/auth/login`.
    """,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=False if settings.DEBUG else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(briefings.router)
app.include_router(notes.router)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["System"])
async def root():
    return {"message": f"{settings.APP_NAME} v{settings.VERSION} — API running"}
