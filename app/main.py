"""FastAPI application factory and health endpoint."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.exceptions import register_exception_handlers
from app.logging_config import setup_logging
from api.routes.auth import router as auth_router
from api.routes.connections import router as connections_router

# Set up structured JSON logging
setup_logging()

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    application = FastAPI(
        title="Text-to-SQL & Document Chat Platform",
        description="Multi-tenant platform for natural language database queries and document chat",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register exception handlers
    register_exception_handlers(application)

    # Include routers
    application.include_router(auth_router)
    application.include_router(connections_router)

    # Health check
    @application.get("/api/health", tags=["health"])
    async def health_check():
        return {"status": "healthy", "service": "text-to-sql-platform"}

    logger.info("Application started")

    return application


app = create_app()
