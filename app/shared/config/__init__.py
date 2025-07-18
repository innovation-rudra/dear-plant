# app/shared/config/__init__.py
"""
Plant Care Application - Configuration Package

Configuration management for the Plant Care Application including:
- Application settings and environment variables
- Database configuration (Supabase PostgreSQL)
- Redis configuration and connection management
- Supabase services configuration (Auth, Storage, Database)

Key Components:
- Settings: Centralized application configuration
- Database: Supabase PostgreSQL configuration
- Redis: Cache and session storage configuration
- Supabase: Auth, Storage, and Database clients

Usage:
    from app.shared.config import get_settings, get_supabase_client, get_redis_client
    
    settings = get_settings()
    supabase = get_supabase_client()
    redis = get_redis_client()
"""

from app.shared.config.settings import get_settings, Settings
from app.shared.config.supabase import (
    get_supabase_client,
    get_supabase_auth,
    get_supabase_storage,
    get_supabase_manager,
    SupabaseManager,
)

# Import database and redis when they're created
try:
    from app.shared.config.database import (
        get_database_config,
        get_database_manager,
        DatabaseConfig,
        DatabaseManager,
    )
except ImportError:
    # Database config not yet available
    pass

try:
    from app.shared.config.redis import (
        get_redis_config,
        get_redis_manager,
        RedisConfig,
        RedisManager as ConfigRedisManager,
    )
except ImportError:
    # Redis config not yet available
    pass

__all__ = [
    # Settings
    "get_settings",
    "Settings",
    
    # Supabase
    "get_supabase_client",
    "get_supabase_auth", 
    "get_supabase_storage",
    "get_supabase_manager",
    "SupabaseManager",
    
    # Database (when available)
    "get_database_config",
    "get_database_manager",
    "DatabaseConfig", 
    "DatabaseManager",
    
    # Redis (when available)
    "get_redis_config",
    "get_redis_manager",
    "RedisConfig",
    "ConfigRedisManager",
]