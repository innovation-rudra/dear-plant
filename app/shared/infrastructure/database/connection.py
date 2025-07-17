"""
Plant Care Application - Database Connection Manager
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
import structlog

from app.shared.config.settings import get_settings
from app.shared.core.exceptions import DatabaseConnectionError

# Get application settings
settings = get_settings()

# Setup logger
logger = structlog.get_logger(__name__)


class DatabaseManager:
    """
    Database connection manager with async support.
    Handles connection pooling, health checks, and session management.
    """

    def __init__(self):
        self._engine: Optional[object] = None
        self._async_session_factory: Optional[async_sessionmaker] = None
        self._initialized = False
        self._health_check_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize database connection and session factory."""
        if self._initialized:
            return

        try:
            # Create async engine with connection pooling
            use_queue_pool = settings.is_production
            pool_class = QueuePool if use_queue_pool else NullPool

            engine_args = {
                "echo": settings.DEBUG,
                "echo_pool": settings.DEBUG,
                "pool_pre_ping": True,
                "poolclass": pool_class,
                "connect_args": {
                    "command_timeout": 30,
                    "server_settings": {
                        "application_name": f"plant_care_{settings.APP_ENV}",
                        "jit": "off",
                    },
                },
                "future": True,
            }

            if use_queue_pool:
                engine_args.update({
                    "pool_size": settings.DATABASE_POOL_SIZE,
                    "max_overflow": settings.DATABASE_MAX_OVERFLOW,
                    "pool_timeout": settings.DATABASE_POOL_TIMEOUT,
                    "pool_recycle": settings.DATABASE_POOL_RECYCLE,
                })

            self._engine = create_async_engine(settings.DATABASE_URL, **engine_args)

            # Create async session factory
            self._async_session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )

            # Set up event listeners
            self._setup_event_listeners()

            # Test connection
            await self._test_connection()

            self._initialized = True
            logger.info("Database manager initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize database manager", error=str(e))
            raise DatabaseConnectionError(f"Failed to initialize database: {str(e)}")

    def _setup_event_listeners(self) -> None:
        """Set up SQLAlchemy event listeners for monitoring."""

        @event.listens_for(self._engine.sync_engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Called when a new database connection is established."""
            logger.debug("New database connection established")

            # asyncpg uses async-style cursor, no context manager support
            cursor = dbapi_connection.cursor()
            cursor.execute("SET timezone TO 'UTC'")
            cursor.execute("SET statement_timeout = 30000")  # 30 seconds
            cursor.execute("SET lock_timeout = 10000")       # 10 seconds

        @event.listens_for(self._engine.sync_engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Called when a connection is checked out from the pool."""
            logger.debug("Connection checked out from pool")

        @event.listens_for(self._engine.sync_engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """Called when a connection is returned to the pool."""
            logger.debug("Connection returned to pool")

        @event.listens_for(self._engine.sync_engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            """Called when a connection is invalidated."""
            logger.warning(
                "Database connection invalidated", error=str(exception) if exception else None
            )

    async def _test_connection(self) -> None:
        """Test database connection."""
        try:
            async with self._engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
            logger.info("Database connection test passed")
        except Exception as e:
            logger.error("Database connection test failed", error=str(e))
            raise DatabaseConnectionError(f"Database connection test failed: {str(e)}")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with automatic cleanup.

        Yields:
            AsyncSession: Database session
        """
        if not self._initialized:
            await self.initialize()

        async with self._async_session_factory() as session:
            try:
                yield session
            except Exception as e:
                logger.error("Session error, rolling back", error=str(e))
                await session.rollback()
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def get_transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session with automatic transaction management.

        Yields:
            AsyncSession: Database session with transaction
        """
        async with self.get_session() as session:
            try:
                await session.begin()
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error("Transaction rolled back", error=str(e))
                raise

    async def health_check(self) -> dict:
        """
        Perform database health check.

        Returns:
            dict: Health check results
        """
        async with self._health_check_lock:
            try:
                # Ensure engine is initialized
                if not self._initialized:
                    await self.initialize()

                if self._engine is None:
                    raise DatabaseConnectionError("Database engine is not initialized")

                start_time = asyncio.get_event_loop().time()

                # Test basic connection
                async with self._engine.begin() as conn:
                    result = await conn.execute(text("SELECT 1"))
                    assert result.scalar() == 1

                # Test connection pool if supported
                pool = self._engine.pool
                pool_status = {}
                if hasattr(pool, "size"):
                    pool_status = {
                        "size": pool.size(),
                        "checked_in": pool.checkedin(),
                        "checked_out": pool.checkedout(),
                        "overflow": pool.overflow(),
                        "invalidated": pool.invalidated(),
                    }

                response_time = asyncio.get_event_loop().time() - start_time

                return {
                    "status": "healthy",
                    "response_time": response_time,
                    "pool_status": pool_status,
                    "database_url": (
                        settings.DATABASE_URL.split("@")[1]
                        if "@" in settings.DATABASE_URL
                        else "masked"
                    ),
                }

            except Exception as e:
                logger.error("Database health check failed", error=str(e))
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "database_url": (
                        settings.DATABASE_URL.split("@")[1]
                        if "@" in settings.DATABASE_URL
                        else "masked"
                    ),
                }

    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            logger.info("Database connections closed")

    def get_engine(self):
        """Get the database engine."""
        return self._engine

    def get_session_factory(self):
        """Get the session factory."""
        return self._async_session_factory


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """
    Get the global database manager instance.

    Returns:
        DatabaseManager: Database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Yields:
        AsyncSession: Database session
    """
    db_manager = get_db_manager()
    async with db_manager.get_transaction() as session:
        yield session


# Database utilities
class DatabaseUtils:
    """Database utility functions."""

    @staticmethod
    async def execute_raw_query(query: str, params: dict = None) -> list:
        """
        Execute raw SQL query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            list: Query results
        """
        db_manager = get_db_manager()
        async with db_manager.get_session() as session:
            result = await session.execute(text(query), params or {})
            return result.fetchall()

    @staticmethod
    async def check_table_exists(table_name: str) -> bool:
        """
        Check if table exists in database.

        Args:
            table_name: Name of the table

        Returns:
            bool: True if table exists
        """
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        );
        """
        result = await DatabaseUtils.execute_raw_query(query, {"table_name": table_name})
        return result[0][0] if result else False

    @staticmethod
    async def get_table_row_count(table_name: str) -> int:
        """
        Get row count for a table.

        Args:
            table_name: Name of the table

        Returns:
            int: Number of rows
        """
        query = f"SELECT COUNT(*) FROM {table_name}"
        result = await DatabaseUtils.execute_raw_query(query)
        return result[0][0] if result else 0

    @staticmethod
    async def get_database_size() -> dict:
        """
        Get database size information.

        Returns:
            dict: Database size information
        """
        query = """
        SELECT 
            pg_size_pretty(pg_database_size(current_database())) as database_size,
            pg_database_size(current_database()) as database_size_bytes
        """
        result = await DatabaseUtils.execute_raw_query(query)
        if result:
            return {"database_size": result[0][0], "database_size_bytes": result[0][1]}
        return {}

    @staticmethod
    async def get_connection_stats() -> dict:
        """
        Get database connection statistics.

        Returns:
            dict: Connection statistics
        """
        query = """
        SELECT 
            COUNT(*) as total_connections,
            COUNT(*) FILTER (WHERE state = 'active') as active_connections,
            COUNT(*) FILTER (WHERE state = 'idle') as idle_connections,
            COUNT(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction
        FROM pg_stat_activity 
        WHERE datname = current_database()
        """
        result = await DatabaseUtils.execute_raw_query(query)
        if result:
            return {
                "total_connections": result[0][0],
                "active_connections": result[0][1],
                "idle_connections": result[0][2],
                "idle_in_transaction": result[0][3],
            }
        return {}


# Connection retry decorator
def retry_db_operation(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator for retrying database operations.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"Database operation failed, retrying in {delay}s",
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            error=str(e),
                        )
                        await asyncio.sleep(delay * (2**attempt))  # Exponential backoff
                    else:
                        logger.error(
                            "Database operation failed after all retries",
                            attempts=max_retries + 1,
                            error=str(e),
                        )

            raise last_exception

        return wrapper

    return decorator


# Database session context manager for manual usage
class DatabaseSession:
    """Context manager for database sessions."""

    def __init__(self, transaction: bool = False):
        self.transaction = transaction
        self.db_manager = get_db_manager()
        self.session = None

    async def __aenter__(self) -> AsyncSession:
        if self.transaction:
            self.session = self.db_manager.get_transaction()
        else:
            self.session = self.db_manager.get_session()

        return await self.session.__aenter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)


# Database migration utilities
class MigrationUtils:
    """Database migration utilities."""

    @staticmethod
    async def run_migration_script(script_path: str) -> None:
        """
        Run a migration script.

        Args:
            script_path: Path to the migration script
        """
        try:
            with open(script_path, "r") as file:
                script_content = file.read()

            db_manager = get_db_manager()
            async with db_manager.get_session() as session:
                await session.execute(text(script_content))
                await session.commit()

            logger.info(f"Migration script executed successfully: {script_path}")

        except Exception as e:
            logger.error(f"Failed to execute migration script: {script_path}", error=str(e))
            raise

    @staticmethod
    async def create_extension(extension_name: str) -> None:
        """
        Create PostgreSQL extension.

        Args:
            extension_name: Name of the extension
        """
        query = f"CREATE EXTENSION IF NOT EXISTS {extension_name}"
        await DatabaseUtils.execute_raw_query(query)
        logger.info(f"Extension created: {extension_name}")

    @staticmethod
    async def setup_database_extensions() -> None:
        """Set up required database extensions."""
        extensions = [
            "uuid-ossp",  # UUID generation
            "pg_trgm",  # Text similarity
            "unaccent",  # Remove accents
            "btree_gin",  # GIN index support
            "btree_gist",  # GiST index support
        ]

        for extension in extensions:
            try:
                await MigrationUtils.create_extension(extension)
            except Exception as e:
                logger.warning(f"Failed to create extension {extension}", error=str(e))


# Database monitoring
class DatabaseMonitor:
    """Database monitoring utilities."""

    @staticmethod
    async def get_slow_queries(limit: int = 10) -> list:
        """
        Get slow queries from pg_stat_statements.

        Args:
            limit: Number of queries to return

        Returns:
            list: Slow queries
        """
        query = """
        SELECT 
            query,
            calls,
            total_time,
            mean_time,
            rows,
            100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
        FROM pg_stat_statements
        WHERE query NOT LIKE '%pg_stat_statements%'
        ORDER BY total_time DESC
        LIMIT :limit
        """
        return await DatabaseUtils.execute_raw_query(query, {"limit": limit})

    @staticmethod
    async def get_table_stats() -> list:
        """
        Get table statistics.

        Returns:
            list: Table statistics
        """
        query = """
        SELECT 
            schemaname,
            tablename,
            attname,
            n_distinct,
            correlation,
            most_common_vals,
            most_common_freqs
        FROM pg_stats
        WHERE schemaname = 'public'
        ORDER BY tablename, attname
        """
        return await DatabaseUtils.execute_raw_query(query)

    @staticmethod
    async def get_index_usage() -> list:
        """
        Get index usage statistics.

        Returns:
            list: Index usage statistics
        """
        query = """
        SELECT 
            schemaname,
            tablename,
            indexname,
            idx_scan,
            idx_tup_read,
            idx_tup_fetch
        FROM pg_stat_user_indexes
        ORDER BY idx_scan DESC
        """
        return await DatabaseUtils.execute_raw_query(query)


# Export utilities
__all__ = [
    "DatabaseManager",
    "get_db_manager",
    "get_db_session",
    "get_db_transaction",
    "DatabaseUtils",
    "DatabaseSession",
    "MigrationUtils",
    "DatabaseMonitor",
    "retry_db_operation",
]


async def get_db_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session with transaction.

    Yields:
        AsyncSession: Database session with transaction
    """
    db_manager = get_db_manager()
    async with db_manager.get_transaction() as session:
        yield session
