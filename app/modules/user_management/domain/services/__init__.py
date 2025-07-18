# app/modules/user_management/domain/services/__init__.py
"""
Plant Care Application - User Management Domain Services

Domain services for user management business logic.
These services orchestrate domain models and handle complex business operations
that don't naturally belong to a single entity.

Services:
- UserService: Core user management operations
- AuthenticationService: Authentication and session management with Supabase
- ProfileService: Profile management and expert verification
- SubscriptionService: Subscription and billing management

Domain services implement business rules and coordinate between multiple entities,
repositories, and external services while maintaining domain purity.
"""

from app.modules.user_management.domain.services.user_service import UserService
from app.modules.user_management.domain.services.auth_service import AuthenticationService
from app.modules.user_management.domain.services.profile_service import ProfileService
from app.modules.user_management.domain.services.subscription_service import SubscriptionService

__all__ = [
    "UserService",
    "AuthenticationService", 
    "ProfileService",
    "SubscriptionService",
]