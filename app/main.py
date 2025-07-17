"""
Plant Care Application - Main FastAPI Application Entry Point
"""
import sys
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import make_asgi_app
import structlog

from app.shared.config.settings import get_settings
from app.shared.core.exceptions import PlantCareException
from app.shared.core.middleware import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    ProcessTimeMiddleware,
    RateLimitMiddleware,
)
from app.shared.infrastructure.database.connection import DatabaseManager
from app.shared.infrastructure.cache.redis_client import RedisManager
from app.shared.utils.logging import setup_logging
from app.api.v1.router import api_router
from app.monitoring.health_checks import router as health_router


# Setup structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Get application settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.
    """
    logger.info("Starting Plant Care API", version=settings.APP_VERSION)
    
    # Initialize database
    try:
        db_manager = DatabaseManager()
        await db_manager.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    # Initialize Redis
    try:
        redis_manager = RedisManager()
        await redis_manager.initialize()
        logger.info("Redis initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Redis", error=str(e))
        raise
    
    # Initialize external services
    try:
        # Initialize Supabase
        from app.shared.config.supabase import get_supabase_client
        supabase_client = get_supabase_client()
        logger.info("Supabase client initialized successfully")
        
        # Initialize background jobs
        try:
            from app.background_jobs.celery_app import celery_app
            logger.info("Celery app initialized successfully")
        except ImportError as e:
            logger.warning("Celery app not available", error=str(e))
        
        # Warm up cache with essential data
        await _warm_up_cache()
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error("Failed to initialize external services", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Plant Care API")
    
    try:
        # Close database connections
        await db_manager.close()
        logger.info("Database connections closed")
        
        # Close Redis connections
        await redis_manager.close()
        logger.info("Redis connections closed")
        
        logger.info("Application shutdown completed successfully")
        
    except Exception as e:
        logger.error("Error during application shutdown", error=str(e))


async def _warm_up_cache() -> None:
    """
    Warm up cache with essential data during startup.
    """
    try:
        # Warm up plant library cache when the module is implemented
        # For now, just warm up basic cache entries
        from app.shared.infrastructure.cache.redis_client import PlantCareCache
        
        # Cache some basic application data
        app_info = {
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "startup_time": "now",
        }
        
        redis_manager = PlantCareCache()
        # This will be replaced with actual plant library warming when implemented
        logger.info("Basic cache warming completed")
        
    except Exception as e:
        logger.warning("Failed to warm up cache", error=str(e))


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Plant Care Application Backend API",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # Add middleware
    _add_middleware(app)
    
    # Add routes
    _add_routes(app)
    
    # Add exception handlers
    _add_exception_handlers(app)
    
    return app


def _add_middleware(app: FastAPI) -> None:
    """
    Add middleware to the FastAPI application.
    """
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS.split(","),
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS.split(","),
        allow_headers=settings.CORS_ALLOW_HEADERS.split(","),
    )
    
    # Gzip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Custom middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ProcessTimeMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(RateLimitMiddleware)


def _add_routes(app: FastAPI) -> None:
    """
    Add routes to the FastAPI application.
    """
    # Health check routes
    app.include_router(health_router, prefix="/health", tags=["health"])
    
    # API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Prometheus metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # Static files (if needed and directory exists)
    if settings.DEBUG:
        import os
        static_dir = "static"
        if os.path.exists(static_dir) and os.path.isdir(static_dir):
            app.mount("/static", StaticFiles(directory=static_dir), name="static")


def _add_exception_handlers(app: FastAPI) -> None:
    """
    Add exception handlers to the FastAPI application.
    """
    
    @app.exception_handler(PlantCareException)
    async def plant_care_exception_handler(request: Request, exc: PlantCareException) -> JSONResponse:
        """
        Handle custom PlantCareException.
        """
        logger.error(
            "PlantCareException occurred",
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            path=request.url.path,
            method=request.method,
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                    "timestamp": exc.timestamp.isoformat(),
                }
            },
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Handle generic exceptions.
        """
        logger.error(
            "Unhandled exception occurred",
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
            method=request.method,
            exc_info=True,
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred",
                    "details": str(exc) if settings.DEBUG else None,
                }
            },
        )


# Create the FastAPI app instance
app = create_app()


@app.get("/")
async def root() -> dict:
    """
    Root endpoint - API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "status": "running",
        "docs_url": "/docs" if settings.DEBUG else None,
        "health_check": "/health/live",
    }


def run() -> None:
    """
    Run the application using uvicorn.
    """
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD and settings.DEBUG,
        debug=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        use_colors=True,
        loop="asyncio",
    )


if __name__ == "__main__":
    run()