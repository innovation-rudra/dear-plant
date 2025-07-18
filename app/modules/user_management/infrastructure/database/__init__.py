# app/modules/user_management/infrastructure/database/__init__.py
"""
Plant Care Application - User Management Database Infrastructure

Database models and repository implementations for user management.
Provides PostgreSQL integration with SQLAlchemy ORM for the Plant Care Application.
"""

from app.modules.user_management.infrastructure.database.models import (
    # Base and utility functions
    Base,
    create_all_tables,
    drop_all_tables,
    get_table_names,
    
    # Database models
    UserModel,
    ProfileModel,
    SubscriptionModel,
    UsageTrackingModel,
    FollowModel,
    SessionModel,
    
    # Enums
    user_role_enum,
    user_status_enum,
    subscription_tier_enum,
    subscription_status_enum,
    billing_cycle_enum,
    profile_status_enum,
    experience_level_enum,
    preferred_units_enum,
    profile_visibility_enum
)

# Repository implementations
from app.modules.user_management.infrastructure.database.user_repository_impl import (
    PostgreSQLUserRepository,
    create_postgresql_user_repository
)
from app.modules.user_management.infrastructure.database.profile_repository_impl import (
    PostgreSQLProfileRepository,
    create_postgresql_profile_repository
)

__all__ = [
    # Base and utilities
    "Base",
    "create_all_tables",
    "drop_all_tables", 
    "get_table_names",
    
    # Models
    "UserModel",
    "ProfileModel", 
    "SubscriptionModel",
    "UsageTrackingModel",
    "FollowModel",
    "SessionModel",
    
    # Enums
    "user_role_enum",
    "user_status_enum",
    "subscription_tier_enum",
    "subscription_status_enum", 
    "billing_cycle_enum",
    "profile_status_enum",
    "experience_level_enum",
    "preferred_units_enum",
    "profile_visibility_enum",
    
    # Repository implementations
    "PostgreSQLUserRepository",
    "PostgreSQLProfileRepository",
    "create_postgresql_user_repository",
    "create_postgresql_profile_repository"
]