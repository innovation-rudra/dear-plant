"""
Plant Care Application - Backend Package Initialization

This package contains the Plant Care Application backend built with FastAPI.
It follows a modular monolith architecture with clear separation of concerns.

Main Components:
- shared/: Shared utilities, configuration, and infrastructure
- modules/: Domain-specific modules (user_management, plant_management, etc.)
- api/: API routing and endpoints
- background_jobs/: Celery tasks and background processing
- monitoring/: Health checks and observability

Technologies:
- FastAPI: Web framework
- SQLAlchemy: ORM for database operations
- Supabase: Authentication, database, and storage
- Redis: Caching and session storage
- Celery: Background task processing
- Structlog: Structured logging
"""

__version__ = "1.0.0"
__author__ = "Plant Care Team"
__email__ = "team@plantcare.com"
__description__ = "Plant Care Application Backend API"

# Package metadata
__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "__description__",
]