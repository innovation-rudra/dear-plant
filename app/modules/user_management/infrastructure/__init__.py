# app/modules/user_management/infrastructure/__init__.py
"""
Plant Care Application - User Management Infrastructure

Infrastructure layer for user management providing database models, repositories,
and external service integrations for the Plant Care Application.
"""

# Database infrastructure
from app.modules.user_management.infrastructure.database import (
    # Models
    UserModel,
    ProfileModel,
    SubscriptionModel,
    UsageTrackingModel,
    FollowModel,
    SessionModel,
    
    # Database utilities
    Base,
    create_all_tables,
    drop_all_tables,
    get_table_names
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

# External service integrations
from app.modules.user_management.infrastructure.external import (
    # Supabase Auth
    SupabaseAuthService,
    SupabaseUser,
    create_supabase_auth_service,
    
    # OAuth
    OAuthProviderManager,
    OAuthUserData,
    oauth_manager,
    get_oauth_manager,
    
    # OAuth Providers
    GoogleOAuthProvider,
    AppleOAuthProvider,
    FacebookOAuthProvider
)

__all__ = [
    # Database Models
    "UserModel",
    "ProfileModel", 
    "SubscriptionModel",
    "UsageTrackingModel",
    "FollowModel",
    "SessionModel",
    
    # Database Utilities
    "Base",
    "create_all_tables",
    "drop_all_tables",
    "get_table_names",
    
    # Repository Implementations
    "PostgreSQLUserRepository",
    "PostgreSQLProfileRepository",
    "create_postgresql_user_repository", 
    "create_postgresql_profile_repository",
    
    # External Services
    "SupabaseAuthService",
    "SupabaseUser",
    "create_supabase_auth_service",
    
    # OAuth
    "OAuthProviderManager",
    "OAuthUserData",
    "oauth_manager",
    "get_oauth_manager",
    "GoogleOAuthProvider",
    "AppleOAuthProvider",
    "FacebookOAuthProvider"
]