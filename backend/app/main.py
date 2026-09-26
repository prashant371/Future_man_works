"""
Personal AI Action Agent — FastAPI Application

Main entry point. Wires up all routers, middleware, and lifecycle events.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.database import init_db, close_db
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.connections import router as connections_router
from app.api.tasks import router as tasks_router

settings = get_settings()

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("personal-ai-agent")


from app.tools.registry import get_registry
from app.tools.github import register_github_tools

# ── Lifecycle ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("🚀 Starting Personal AI Action Agent...")
    await init_db()
    logger.info("✅ Database tables created / verified.")
    
    # Register Tools
    registry = get_registry()
    register_github_tools(registry)
    logger.info("✅ Tools registered.")
    
    yield
    logger.info("🛑 Shutting down...")
    await close_db()


# ── FastAPI App ───────────────────────────────────────────────
app = FastAPI(
    title="Personal AI Action Agent",
    description="AI-powered personal automation platform for managing GitHub, LinkedIn, and more.",
    version="0.1.0",
    lifespan=lifespan,
)

# ── CORS Middleware ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(connections_router)
app.include_router(tasks_router)


# ── Health Check ──────────────────────────────────────────────
@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "personal-ai-agent",
        "version": "0.1.0",
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": "Personal AI Action Agent API",
        "docs": "/docs",
        "health": "/api/health",
    }
