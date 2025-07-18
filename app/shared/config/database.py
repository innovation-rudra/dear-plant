# app/shared/config/database.py
"""
Plant Care Application - Database Configuration

Database configuration and connection management for Plant Care Application.
Integrates with Supabase PostgreSQL database and provides connection pooling,
health monitoring, and Plant Care specific database utilities.

This configuration works alongside the Supabase client for complete database access.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from functools import lru_cache
from urllib.parse import urlparse

import asyncpg
from asyncpg import Pool, Connection
import structlog

from app.shared.config.settings import get_settings
from app.shared.core.exceptions import (
    DatabaseError, 
    DatabaseConnectionError,
    DatabaseTransactionError,
    ConfigurationError
)

# Get application settings
settings = get_settings()

# Setup logger
logger = structlog.get_logger(__name__)


class DatabaseConfig:
    """
    Database configuration for Plant Care Application.
    Manages Supabase PostgreSQL connection settings and pool configuration.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate database configuration."""
        if not self.settings.DATABASE_URL:
            raise ConfigurationError("DATABASE_URL is required")
        
        # Parse database URL to validate format
        try:
            parsed = urlparse(self.settings.DATABASE_URL)
            if not all([parsed.scheme, parsed.hostname, parsed.username]):
                raise ValueError("Invalid DATABASE_URL format")
        except Exception as e:
            raise ConfigurationError(f"Invalid DATABASE_URL: {str(e)}")
    
    @property
    def connection_kwargs(self) -> Dict[str, Any]:
        """
        Get database connection parameters for Plant Care Application.
        
        Returns:
            Dict[str, Any]: Connection parameters for asyncpg
        """
        parsed = urlparse(self.settings.DATABASE_URL)
        
        return {
            "host": parsed.hostname,
            "port": parsed.port or 5432,
            "user": parsed.username,
            "password": parsed.password,
            "database": parsed.path.lstrip('/') if parsed.path else 'postgres',
            "ssl": "require",  # Supabase requires SSL
            "command_timeout": 60,
            "server_settings": {
                "application_name": f"plant_care_api_{self.settings.APP_ENV}",
                "jit": "off",  # Disable JIT for better performance on small queries
            }
        }
    
    @property
    def pool_kwargs(self) -> Dict[str, Any]:
        """
        Get connection pool parameters.
        
        Returns:
            Dict[str, Any]: Pool configuration for Plant Care Application
        """
        return {
            "min_size": max(1, self.settings.DATABASE_POOL_SIZE // 4),
            "max_size": self.settings.DATABASE_POOL_SIZE,
            "max_queries": 50000,  # Queries per connection before recycling
            "max_inactive_connection_lifetime": self.settings.DATABASE_POOL_RECYCLE,
            "timeout": self.settings.DATABASE_POOL_TIMEOUT,
            "command_timeout": 60,
            "setup": self._setup_connection,
        }
    
    async def _setup_connection(self, connection: Connection) -> None:
        """
        Setup connection for Plant Care Application specific optimizations.
        
        Args:
            connection: Database connection to setup
        """
        try:
            # Set Plant Care specific connection settings
            await connection.execute("SET timezone = 'UTC'")
            await connection.execute("SET statement_timeout = '30s'")
            await connection.execute("SET lock_timeout = '10s'")
            await connection.execute("SET idle_in_transaction_session_timeout = '5min'")
            
            # Plant Care specific settings for better performance
            await connection.execute("SET default_statistics_target = 100")
            await connection.execute("SET random_page_cost = 1.1")  # SSD optimized
            
            logger.debug("Database connection configured for Plant Care Application")
            
        except Exception as e:
            logger.error("Failed to setup database connection", error=str(e))
            raise DatabaseConnectionError(f"Connection setup failed: {str(e)}")


class DatabaseManager:
    """
    Database manager for Plant Care Application.
    Provides connection pooling, health monitoring, and database operations.
    """
    
    def __init__(self):
        self.config = DatabaseConfig()
        self._pool: Optional[Pool] = None
        self._initialized = False
        self._health_check_lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize database connection pool."""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing database manager for Plant Care Application")
            
            # Create connection pool
            self._pool = await asyncpg.create_pool(
                **self.config.connection_kwargs,
                **self.config.pool_kwargs
            )
            
            # Verify pool is working
            await self._verify_pool()
            
            self._initialized = True
            logger.info("Database manager initialized successfully", 
                       pool_size=self.config.pool_kwargs["max_size"])
            
        except Exception as e:
            logger.error("Failed to initialize database manager", error=str(e))
            raise DatabaseConnectionError(f"Database initialization failed: {str(e)}")
    
    async def _verify_pool(self) -> None:
        """Verify database pool is working."""
        try:
            async with self._pool.acquire() as connection:
                result = await connection.fetchval("SELECT 1")
                if result != 1:
                    raise ValueError("Database verification query failed")
                
                # Test Plant Care specific functionality
                await connection.fetchval("SELECT NOW()")
                
            logger.info("Database pool verification successful")
            
        except Exception as e:
            logger.error("Database pool verification failed", error=str(e))
            raise DatabaseConnectionError(f"Pool verification failed: {str(e)}")
    
    async def get_pool(self) -> Pool:
        """
        Get database connection pool.
        
        Returns:
            Pool: Database connection pool
            
        Raises:
            DatabaseConnectionError: If pool is not initialized
        """
        if not self._initialized or not self._pool:
            raise DatabaseConnectionError("Database manager not initialized")
        
        return self._pool
    
    async def get_connection(self) -> Connection:
        """
        Get database connection from pool.
        
        Returns:
            Connection: Database connection
            
        Raises:
            DatabaseConnectionError: If unable to get connection
        """
        try:
            pool = await self.get_pool()
            return await pool.acquire()
        except Exception as e:
            logger.error("Failed to acquire database connection", error=str(e))
            raise DatabaseConnectionError(f"Failed to get connection: {str(e)}")
    
    async def execute_query(self, query: str, *args) -> Any:
        """
        Execute a database query.
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            
        Returns:
            Any: Query result
            
        Raises:
            DatabaseError: If query execution fails
        """
        try:
            async with self._pool.acquire() as connection:
                return await connection.fetchval(query, *args)
        except Exception as e:
            logger.error("Database query failed", query=query, error=str(e))
            raise DatabaseError(f"Query execution failed: {str(e)}")
    
    async def execute_many(self, query: str, args_list: List) -> None:
        """
        Execute query with multiple parameter sets.
        
        Args:
            query: SQL query to execute
            args_list: List of parameter tuples
            
        Raises:
            DatabaseError: If execution fails
        """
        try:
            async with self._pool.acquire() as connection:
                await connection.executemany(query, args_list)
        except Exception as e:
            logger.error("Database executemany failed", query=query, error=str(e))
            raise DatabaseError(f"Bulk execution failed: {str(e)}")
    
    async def transaction(self) -> Any:
        """
        Get database transaction context.
        
        Returns:
            asyncpg.Transaction: Database transaction
            
        Raises:
            DatabaseTransactionError: If transaction creation fails
        """
        try:
            connection = await self.get_connection()
            return connection.transaction()
        except Exception as e:
            logger.error("Failed to create transaction", error=str(e))
            raise DatabaseTransactionError(f"Transaction creation failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check for Plant Care Application.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        async with self._health_check_lock:
            start_time = time.time()
            
            try:
                if not self._pool:
                    return {
                        "status": "unhealthy",
                        "error": "Database pool not initialized",
                        "response_time": 0
                    }
                
                # Test basic connectivity
                async with self._pool.acquire() as connection:
                    # Basic health check
                    await connection.fetchval("SELECT 1")
                    
                    # Plant Care specific health checks
                    now = await connection.fetchval("SELECT NOW()")
                    
                    # Check if we can access user tables (basic schema check)
                    table_exists = await connection.fetchval("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'profiles'
                        )
                    """)
                
                response_time = time.time() - start_time
                
                # Get pool status
                pool_status = {
                    "size": self._pool.get_size(),
                    "max_size": self._pool.get_max_size(),
                    "min_size": self._pool.get_min_size(),
                    "idle_connections": self._pool.get_idle_size(),
                }
                
                return {
                    "status": "healthy",
                    "response_time": response_time,
                    "timestamp": now.isoformat() if now else None,
                    "pool_status": pool_status,
                    "schema_ready": bool(table_exists),
                    "database_type": "supabase_postgresql"
                }
                
            except Exception as e:
                response_time = time.time() - start_time
                logger.error("Database health check failed", error=str(e))
                
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "response_time": response_time,
                    "database_type": "supabase_postgresql"
                }
    
    async def close(self) -> None:
        """Close database connection pool."""
        if self._pool:
            logger.info("Closing database connection pool")
            await self._pool.close()
            self._pool = None
            self._initialized = False


# Global database manager instance
_database_manager: Optional[DatabaseManager] = None


@lru_cache()
def get_database_config() -> DatabaseConfig:
    """
    Get database configuration for Plant Care Application.
    
    Returns:
        DatabaseConfig: Database configuration instance
    """
    return DatabaseConfig()


def get_database_manager() -> DatabaseManager:
    """
    Get database manager singleton for Plant Care Application.
    
    Returns:
        DatabaseManager: Database manager instance
    """
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseManager()
    return _database_manager


async def get_db_connection() -> Connection:
    """
    Get database connection for Plant Care Application.
    
    Returns:
        Connection: Database connection
    """
    manager = get_database_manager()
    return await manager.get_connection()


async def get_db_pool() -> Pool:
    """
    Get database pool for Plant Care Application.
    
    Returns:
        Pool: Database connection pool
    """
    manager = get_database_manager()
    return await manager.get_pool()


# Plant Care Application specific database utilities
class PlantCareDatabase:
    """Plant Care Application specific database utilities."""
    
    @staticmethod
    async def ensure_user_exists(user_id: str, email: str, connection: Connection = None) -> bool:
        """
        Ensure user exists in Plant Care database.
        
        Args:
            user_id: Supabase user ID
            email: User email
            connection: Optional database connection
            
        Returns:
            bool: True if user exists or was created
        """
        query = """
            INSERT INTO profiles (user_id, email, created_at, updated_at)
            VALUES ($1, $2, NOW(), NOW())
            ON CONFLICT (user_id) DO NOTHING
            RETURNING user_id
        """
        
        try:
            if connection:
                result = await connection.fetchval(query, user_id, email)
            else:
                manager = get_database_manager()
                result = await manager.execute_query(query, user_id, email)
            
            return True
        except Exception as e:
            logger.error("Failed to ensure user exists", user_id=user_id, error=str(e))
            return False
    
    @staticmethod
    async def get_user_plant_count(user_id: str, connection: Connection = None) -> int:
        """
        Get user's plant count for Plant Care Application.
        
        Args:
            user_id: User ID
            connection: Optional database connection
            
        Returns:
            int: Number of plants user has
        """
        query = "SELECT COUNT(*) FROM plants WHERE user_id = $1 AND deleted_at IS NULL"
        
        try:
            if connection:
                result = await connection.fetchval(query, user_id)
            else:
                manager = get_database_manager()
                result = await manager.execute_query(query, user_id)
            
            return result or 0
        except Exception as e:
            logger.error("Failed to get user plant count", user_id=user_id, error=str(e))
            return 0