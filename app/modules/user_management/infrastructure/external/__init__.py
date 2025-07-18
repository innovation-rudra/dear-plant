# app/modules/user_management/infrastructure/external/__init__.py
"""
Plant Care Application - External Infrastructure

External service integrations for user management including Supabase authentication,
OAuth providers, and third-party service integrations.
"""

from app.modules.user_management.infrastructure.external.supabase_auth import (
    SupabaseAuthService,
    SupabaseUser,
    create_supabase_auth_service
)
from app.modules.user_management.infrastructure.external.oauth_providers import (
    # OAuth providers
    GoogleOAuthProvider,
    AppleOAuthProvider,
    FacebookOAuthProvider,
    BaseOAuthProvider,
    
    # OAuth data structures
    OAuthUserData,
    
    # OAuth manager
    OAuthProviderManager,
    oauth_manager,
    
    # Factory functions
    get_oauth_manager,
    create_google_oauth_provider,
    create_apple_oauth_provider,
    create_facebook_oauth_provider
)

__all__ = [
    # Supabase Auth
    "SupabaseAuthService",
    "SupabaseUser",
    "create_supabase_auth_service",
    
    # OAuth Providers
    "GoogleOAuthProvider",
    "AppleOAuthProvider", 
    "FacebookOAuthProvider",
    "BaseOAuthProvider",
    
    # OAuth Data
    "OAuthUserData",
    
    # OAuth Manager
    "OAuthProviderManager",
    "oauth_manager",
    
    # Factory Functions
    "get_oauth_manager",
    "create_google_oauth_provider",
    "create_apple_oauth_provider",
    "create_facebook_oauth_provider"
]