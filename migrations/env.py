"""
Plant Care Application - Alembic Migration Environment
"""
import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

# Import all models to ensure they are registered with SQLAlchemy
from app.shared.infrastructure.database.models import Base
from app.modules.user_management.infrastructure.database.models import *
from app.modules.plant_management.infrastructure.database.models import *
from app.modules.care_management.infrastructure.database.models import *
from app.modules.health_monitoring.infrastructure.database.models import *
from app.modules.growth_tracking.infrastructure.database.models import *
from app.modules.community_social.infrastructure.database.models import *
from app.modules.ai_smart_features.infrastructure.database.models import *
from app.modules.weather_environmental.infrastructure.database.models import *
from app.modules.analytics_insights.infrastructure.database.models import *
from app.modules.notification_communication.infrastructure.database.models import *
from app.modules.payment_subscription.infrastructure.database.models import *
from app.modules.content_management.infrastructure.database.models import *

# Import settings
from app.shared.config.settings import get_settings

# Get application settings
settings = get_settings()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the SQLAlchemy URL from environment variable
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
        transaction_per_migration=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a database connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,
        transaction_per_migration=True,
        include_schemas=True,
        # Include object filters for better migration control
        include_object=include_object,
        # Custom naming convention
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def include_object(object, name, type_, reflected, compare_to):
    """Filter objects to include in migrations."""
    # Skip temporary tables
    if type_ == "table" and name.startswith("tmp_"):
        return False
    
    # Skip certain indexes that are auto-generated
    if type_ == "index" and name.startswith("ix_"):
        return False
    
    # Skip foreign key constraints with auto-generated names
    if type_ == "foreign_key_constraint" and name.startswith("fk_"):
        return False
    
    return True


def render_item(type_, obj, autogen_context):
    """Render items with custom formatting."""
    if type_ == "type" and hasattr(obj, "name"):
        # Custom enum rendering
        if obj.name.endswith("_enum"):
            return f"sa.Enum({obj.name})"
    
    # Use default rendering for other items
    return False


async def run_async_migrations() -> None:
    """Run migrations in async mode."""
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Check if we're running in async mode
    if os.environ.get("ALEMBIC_ASYNC", "false").lower() == "true":
        asyncio.run(run_async_migrations())
    else:
        # Synchronous mode for compatibility
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )

        with connectable.connect() as connection:
            do_run_migrations(connection)


# Custom migration utilities
def upgrade_schema():
    """Upgrade database schema to latest version."""
    from alembic.command import upgrade
    from alembic.config import Config
    
    alembic_cfg = Config("alembic.ini")
    upgrade(alembic_cfg, "head")


def downgrade_schema(revision: str = "-1"):
    """Downgrade database schema to specified revision."""
    from alembic.command import downgrade
    from alembic.config import Config
    
    alembic_cfg = Config("alembic.ini")
    downgrade(alembic_cfg, revision)


def generate_migration(message: str, autogenerate: bool = True):
    """Generate a new migration file."""
    from alembic.command import revision
    from alembic.config import Config
    
    alembic_cfg = Config("alembic.ini")
    revision(alembic_cfg, message=message, autogenerate=autogenerate)


def get_current_revision():
    """Get current database revision."""
    from alembic.command import current
    from alembic.config import Config
    
    alembic_cfg = Config("alembic.ini")
    return current(alembic_cfg)


def get_migration_history():
    """Get migration history."""
    from alembic.command import history
    from alembic.config import Config
    
    alembic_cfg = Config("alembic.ini")
    return history(alembic_cfg)


# Environment-specific configurations
if settings.APP_ENV == "production":
    # Production-specific migration settings
    def include_object_prod(object, name, type_, reflected, compare_to):
        """Production-specific object filtering."""
        # Skip development tables
        if type_ == "table" and name.startswith("dev_"):
            return False
        
        # Skip test tables
        if type_ == "table" and name.startswith("test_"):
            return False
        
        return include_object(object, name, type_, reflected, compare_to)
    
    # Override include_object for production
    include_object = include_object_prod

elif settings.APP_ENV == "development":
    # Development-specific migration settings
    def include_object_dev(object, name, type_, reflected, compare_to):
        """Development-specific object filtering."""
        # Include all objects in development
        return True
    
    # Override include_object for development
    include_object = include_object_dev

elif settings.APP_ENV == "testing":
    # Test-specific migration settings
    def include_object_test(object, name, type_, reflected, compare_to):
        """Test-specific object filtering."""
        # Include test tables
        if type_ == "table" and name.startswith("test_"):
            return True
        
        return include_object(object, name, type_, reflected, compare_to)
    
    # Override include_object for testing
    include_object = include_object_test


# Run migrations based on context
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

# app/modules/user_management/infrastructure/database/models.py
"""
User Management - Database Models
Placeholder file - will be implemented when we build the user management module.
"""
# Empty for now - will be populated when we implement the module

# app/modules/plant_management/infrastructure/database/models.py
"""
Plant Management - Database Models
Placeholder file - will be implemented when we build the plant management module.
"""
# Empty for now - will be populated when we implement the module

# app/modules/care_management/infrastructure/database/models.py
"""
Care Management - Database Models
Placeholder file - will be implemented when we build the care management module.
"""
# Empty for now - will be populated when we implement the module

# app/modules/health_monitoring/infrastructure/database/models.py
"""
Health Monitoring - Database Models
Placeholder file - will be implemented when we build the health monitoring module.
"""
# Empty for now - will be populated when we implement the module

# app/modules/growth_tracking/infrastructure/database/models.py
"""
Growth Tracking - Database Models
Placeholder file - will be implemented when we build the growth tracking module.
"""
# Empty for now - will be populated when we implement the module

# app/modules/community_social/infrastructure/database/models.py
"""
Community Social - Database Models
Placeholder file - will be implemented when we build the community social module.
"""
# Empty for now - will be populated when we implement the module

# app/modules/ai_smart_features/infrastructure/database/models.py
"""
AI Smart Features - Database Models
Placeholder file - will be implemented when we build the AI features module.
"""
# Empty for now - will be populated when we implement the module

# app/modules/weather_environmental/infrastructure/database/models.py
"""
Weather Environmental - Database Models
Placeholder file - will be implemented when we build the weather module.
"""
# Empty for now - will be populated when we implement the module

# app/modules/analytics_insights/infrastructure/database/models.py
"""
Analytics Insights - Database Models
Placeholder file - will be implemented when we build the analytics module.
"""
# Empty for now - will be populated when we implement the module

# app/modules/notification_communication/infrastructure/database/models.py
"""
Notification Communication - Database Models
Placeholder file - will be implemented when we build the notification module.
"""
# Empty for now - will be populated when we implement the module

# app/modules/payment_subscription/infrastructure/database/models.py
"""
Payment Subscription - Database Models
Placeholder file - will be implemented when we build the payment module.
"""
# Empty for now - will be populated when we implement the module

# app/modules/content_management/infrastructure/database/models.py
"""
Content Management - Database Models
Placeholder file - will be implemented when we build the content management module.
"""
# Empty for now - will be populated when we implement the module