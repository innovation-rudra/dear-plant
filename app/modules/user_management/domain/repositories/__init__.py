# app/modules/user_management/domain/repositories/__init__.py
"""
Plant Care Application - User Management Repository Interfaces

Repository interfaces for user management domain.
These define the contracts for data access without coupling to specific implementations.

Repositories:
- UserRepository: User entity persistence and retrieval
- ProfileRepository: Profile entity persistence and retrieval

Following the Repository pattern from Domain-Driven Design.
"""

from app.modules.user_management.domain.repositories.user_repository import UserRepository
from app.modules.user_management.domain.repositories.profile_repository import ProfileRepository

__all__ = [
    "UserRepository",
    "ProfileRepository",
]