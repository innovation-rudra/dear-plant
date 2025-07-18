# app/modules/user_management/infrastructure/database/user_repository_impl.py
"""
Plant Care Application - PostgreSQL User Repository Implementation

Concrete implementation of UserRepository interface using SQLAlchemy and PostgreSQL.
Handles all user data persistence operations for the Plant Care Application.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import structlog

from app.modules.user_management.domain.models.user import User, UserRole, UserStatus
from app.modules.user_management.domain.models.subscription import Subscription, SubscriptionTier, SubscriptionStatus, BillingCycle
from app.modules.user_management.domain.repositories.user_repository import UserRepository
from app.modules.user_management.infrastructure.database.models import (
    UserModel, SubscriptionModel, ProfileModel, UsageTrackingModel, SessionModel
)
from app.shared.core.exceptions import (
    DatabaseError, ResourceNotFoundError, ValidationError, BusinessLogicError
)
from app.shared.infrastructure.database.connection import get_database_session

# Setup logger
logger = structlog.get_logger(__name__)


class PostgreSQLUserRepository(UserRepository):
    """
    PostgreSQL implementation of UserRepository for Plant Care Application.
    Provides CRUD operations and complex queries for user management.
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy session (optional, will create if not provided)
        """
        self._session = session
    
    async def _get_session(self) -> Session:
        """Get database session."""
        if self._session:
            return self._session
        return await get_database_session()
    
    async def create(self, user: User) -> User:
        """
        Create a new user in the database.
        
        Args:
            user: User domain model to create
            
        Returns:
            User: Created user with updated database information
            
        Raises:
            DatabaseError: If user creation fails
            ValidationError: If user data is invalid
        """
        try:
            session = await self._get_session()
            
            logger.info("Creating user in database", user_id=user.user_id, email=user.email)
            
            # Convert domain model to database model
            user_model = UserModel(
                user_id=user.user_id,
                email=user.email,
                supabase_user_id=user.supabase_user_id,
                password_hash=user.password_hash,
                provider=user.provider,
                role=user.role.value,
                status=user.status.value,
                is_verified=user.is_verified,
                is_onboarded=user.is_onboarded,
                plant_limit=user.plant_limit,
                created_at=user.created_at,
                updated_at=user.updated_at,
                last_login_at=user.last_login_at,
                last_activity_at=user.last_activity_at,
                email_verified_at=user.email_verified_at,
                onboarded_at=user.onboarded_at,
                deleted_at=user.deleted_at,
                deletion_reason=user.deletion_reason,
                failed_login_attempts=getattr(user, 'failed_login_attempts', 0),
                locked_until=getattr(user, 'locked_until', None)
            )
            
            # Create subscription if provided
            if user.subscription:
                subscription_model = SubscriptionModel(
                    subscription_id=user.subscription.subscription_id,
                    user_id=user.user_id,
                    tier=user.subscription.tier.value,
                    status=user.subscription.status.value,
                    billing_cycle=user.subscription.billing_cycle.value if user.subscription.billing_cycle else None,
                    price=user.subscription.price,
                    currency=user.subscription.currency,
                    trial_end_date=user.subscription.trial_end_date,
                    current_period_start=user.subscription.current_period_start,
                    current_period_end=user.subscription.current_period_end,
                    next_billing_date=user.subscription.next_billing_date,
                    payment_method_id=user.subscription.payment_method_id,
                    last_payment_date=user.subscription.last_payment_date,
                    last_payment_amount=user.subscription.last_payment_amount,
                    cancel_at_period_end=user.subscription.cancel_at_period_end,
                    cancelled_at=user.subscription.cancelled_at,
                    cancellation_reason=user.subscription.cancellation_reason,
                    created_at=user.subscription.created_at,
                    updated_at=user.subscription.updated_at
                )
                user_model.subscription = subscription_model
            
            session.add(user_model)
            await session.commit()
            await session.refresh(user_model)
            
            # Convert back to domain model
            created_user = await self._model_to_domain(user_model)
            
            logger.info("User created successfully", user_id=created_user.user_id)
            
            return created_user
            
        except IntegrityError as e:
            await session.rollback()
            logger.error("User creation failed - integrity error", user_id=user.user_id, error=str(e))
            if "email" in str(e):
                raise ValidationError("Email already exists")
            elif "supabase_user_id" in str(e):
                raise ValidationError("Supabase user ID already exists")
            else:
                raise DatabaseError(f"User creation failed: {str(e)}")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("User creation failed - database error", user_id=user.user_id, error=str(e))
            raise DatabaseError(f"Failed to create user: {str(e)}")
        except Exception as e:
            await session.rollback()
            logger.error("User creation failed - unexpected error", user_id=user.user_id, error=str(e))
            raise DatabaseError(f"Unexpected error creating user: {str(e)}")
    
    async def update(self, user: User) -> User:
        """
        Update an existing user in the database.
        
        Args:
            user: User domain model with updates
            
        Returns:
            User: Updated user
            
        Raises:
            ResourceNotFoundError: If user not found
            DatabaseError: If update fails
        """
        try:
            session = await self._get_session()
            
            logger.info("Updating user in database", user_id=user.user_id)
            
            # Find existing user
            user_model = await session.get(UserModel, user.user_id)
            if not user_model:
                raise ResourceNotFoundError(f"User not found: {user.user_id}")
            
            # Update fields
            user_model.email = user.email
            user_model.supabase_user_id = user.supabase_user_id
            user_model.password_hash = user.password_hash
            user_model.provider = user.provider
            user_model.role = user.role.value
            user_model.status = user.status.value
            user_model.is_verified = user.is_verified
            user_model.is_onboarded = user.is_onboarded
            user_model.plant_limit = user.plant_limit
            user_model.updated_at = user.updated_at
            user_model.last_login_at = user.last_login_at
            user_model.last_activity_at = user.last_activity_at
            user_model.email_verified_at = user.email_verified_at
            user_model.onboarded_at = user.onboarded_at
            user_model.deleted_at = user.deleted_at
            user_model.deletion_reason = user.deletion_reason
            user_model.failed_login_attempts = getattr(user, 'failed_login_attempts', 0)
            user_model.locked_until = getattr(user, 'locked_until', None)
            
            # Update subscription if provided
            if user.subscription:
                if user_model.subscription:
                    # Update existing subscription
                    sub_model = user_model.subscription
                    sub_model.tier = user.subscription.tier.value
                    sub_model.status = user.subscription.status.value
                    sub_model.billing_cycle = user.subscription.billing_cycle.value if user.subscription.billing_cycle else None
                    sub_model.price = user.subscription.price
                    sub_model.currency = user.subscription.currency
                    sub_model.trial_end_date = user.subscription.trial_end_date
                    sub_model.current_period_start = user.subscription.current_period_start
                    sub_model.current_period_end = user.subscription.current_period_end
                    sub_model.next_billing_date = user.subscription.next_billing_date
                    sub_model.payment_method_id = user.subscription.payment_method_id
                    sub_model.last_payment_date = user.subscription.last_payment_date
                    sub_model.last_payment_amount = user.subscription.last_payment_amount
                    sub_model.cancel_at_period_end = user.subscription.cancel_at_period_end
                    sub_model.cancelled_at = user.subscription.cancelled_at
                    sub_model.cancellation_reason = user.subscription.cancellation_reason
                    sub_model.updated_at = user.subscription.updated_at
                else:
                    # Create new subscription
                    subscription_model = SubscriptionModel(
                        subscription_id=user.subscription.subscription_id,
                        user_id=user.user_id,
                        tier=user.subscription.tier.value,
                        status=user.subscription.status.value,
                        billing_cycle=user.subscription.billing_cycle.value if user.subscription.billing_cycle else None,
                        price=user.subscription.price,
                        currency=user.subscription.currency,
                        trial_end_date=user.subscription.trial_end_date,
                        current_period_start=user.subscription.current_period_start,
                        current_period_end=user.subscription.current_period_end,
                        next_billing_date=user.subscription.next_billing_date,
                        payment_method_id=user.subscription.payment_method_id,
                        created_at=user.subscription.created_at,
                        updated_at=user.subscription.updated_at
                    )
                    user_model.subscription = subscription_model
            
            await session.commit()
            await session.refresh(user_model)
            
            # Convert back to domain model
            updated_user = await self._model_to_domain(user_model)
            
            logger.info("User updated successfully", user_id=updated_user.user_id)
            
            return updated_user
            
        except ResourceNotFoundError:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error("User update failed - integrity error", user_id=user.user_id, error=str(e))
            raise DatabaseError(f"User update failed: {str(e)}")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("User update failed - database error", user_id=user.user_id, error=str(e))
            raise DatabaseError(f"Failed to update user: {str(e)}")
        except Exception as e:
            await session.rollback()
            logger.error("User update failed - unexpected error", user_id=user.user_id, error=str(e))
            raise DatabaseError(f"Unexpected error updating user: {str(e)}")
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Find user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        try:
            session = await self._get_session()
            
            user_model = await session.query(UserModel).options(
                selectinload(UserModel.subscription),
                selectinload(UserModel.profile)
            ).filter(UserModel.user_id == user_id).first()
            
            if not user_model:
                return None
            
            return await self._model_to_domain(user_model)
            
        except SQLAlchemyError as e:
            logger.error("Find user by ID failed", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to find user: {str(e)}")
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        try:
            session = await self._get_session()
            
            user_model = await session.query(UserModel).options(
                selectinload(UserModel.subscription),
                selectinload(UserModel.profile)
            ).filter(UserModel.email == email).first()
            
            if not user_model:
                return None
            
            return await self._model_to_domain(user_model)
            
        except SQLAlchemyError as e:
            logger.error("Find user by email failed", email=email, error=str(e))
            raise DatabaseError(f"Failed to find user by email: {str(e)}")
    
    async def find_by_supabase_id(self, supabase_user_id: str) -> Optional[User]:
        """
        Find user by Supabase user ID.
        
        Args:
            supabase_user_id: Supabase user ID to search for
            
        Returns:
            Optional[User]: User if found, None otherwise
        """
        try:
            session = await self._get_session()
            
            user_model = await session.query(UserModel).options(
                selectinload(UserModel.subscription),
                selectinload(UserModel.profile)
            ).filter(UserModel.supabase_user_id == supabase_user_id).first()
            
            if not user_model:
                return None
            
            return await self._model_to_domain(user_model)
            
        except SQLAlchemyError as e:
            logger.error("Find user by Supabase ID failed", supabase_id=supabase_user_id, error=str(e))
            raise DatabaseError(f"Failed to find user by Supabase ID: {str(e)}")
    
    async def find_by_role(self, role: UserRole, limit: int = 100, offset: int = 0) -> List[User]:
        """
        Find users by role.
        
        Args:
            role: User role to search for
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[User]: List of users with the specified role
        """
        try:
            session = await self._get_session()
            
            user_models = await session.query(UserModel).options(
                selectinload(UserModel.subscription),
                selectinload(UserModel.profile)
            ).filter(
                UserModel.role == role.value
            ).offset(offset).limit(limit).all()
            
            users = []
            for user_model in user_models:
                user = await self._model_to_domain(user_model)
                users.append(user)
            
            return users
            
        except SQLAlchemyError as e:
            logger.error("Find users by role failed", role=role.value, error=str(e))
            raise DatabaseError(f"Failed to find users by role: {str(e)}")
    
    async def find_by_status(self, status: UserStatus, limit: int = 100, offset: int = 0) -> List[User]:
        """
        Find users by status.
        
        Args:
            status: User status to search for
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[User]: List of users with the specified status
        """
        try:
            session = await self._get_session()
            
            user_models = await session.query(UserModel).options(
                selectinload(UserModel.subscription),
                selectinload(UserModel.profile)
            ).filter(
                UserModel.status == status.value
            ).offset(offset).limit(limit).all()
            
            users = []
            for user_model in user_models:
                user = await self._model_to_domain(user_model)
                users.append(user)
            
            return users
            
        except SQLAlchemyError as e:
            logger.error("Find users by status failed", status=status.value, error=str(e))
            raise DatabaseError(f"Failed to find users by status: {str(e)}")
    
    async def find_active_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """
        Find active users (status = ACTIVE).
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[User]: List of active users
        """
        return await self.find_by_status(UserStatus.ACTIVE, limit, offset)
    
    async def find_users_with_subscription_tier(self, tier: SubscriptionTier, 
                                              limit: int = 100, offset: int = 0) -> List[User]:
        """
        Find users with specific subscription tier.
        
        Args:
            tier: Subscription tier to search for
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[User]: List of users with the specified subscription tier
        """
        try:
            session = await self._get_session()
            
            user_models = await session.query(UserModel).options(
                selectinload(UserModel.subscription),
                selectinload(UserModel.profile)
            ).join(SubscriptionModel).filter(
                SubscriptionModel.tier == tier.value
            ).offset(offset).limit(limit).all()
            
            users = []
            for user_model in user_models:
                user = await self._model_to_domain(user_model)
                users.append(user)
            
            return users
            
        except SQLAlchemyError as e:
            logger.error("Find users by subscription tier failed", tier=tier.value, error=str(e))
            raise DatabaseError(f"Failed to find users by subscription tier: {str(e)}")
    
    async def find_recently_registered(self, days: int = 7, limit: int = 100) -> List[User]:
        """
        Find recently registered users.
        
        Args:
            days: Number of days to look back
            limit: Maximum number of results
            
        Returns:
            List[User]: List of recently registered users
        """
        try:
            session = await self._get_session()
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            user_models = await session.query(UserModel).options(
                selectinload(UserModel.subscription),
                selectinload(UserModel.profile)
            ).filter(
                UserModel.created_at >= cutoff_date
            ).order_by(desc(UserModel.created_at)).limit(limit).all()
            
            users = []
            for user_model in user_models:
                user = await self._model_to_domain(user_model)
                users.append(user)
            
            return users
            
        except SQLAlchemyError as e:
            logger.error("Find recently registered users failed", days=days, error=str(e))
            raise DatabaseError(f"Failed to find recently registered users: {str(e)}")
    
    async def find_inactive_users(self, days: int = 30, limit: int = 100) -> List[User]:
        """
        Find users who haven't been active recently.
        
        Args:
            days: Number of days of inactivity
            limit: Maximum number of results
            
        Returns:
            List[User]: List of inactive users
        """
        try:
            session = await self._get_session()
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            user_models = await session.query(UserModel).options(
                selectinload(UserModel.subscription),
                selectinload(UserModel.profile)
            ).filter(
                and_(
                    UserModel.status == UserStatus.ACTIVE.value,
                    or_(
                        UserModel.last_activity_at < cutoff_date,
                        UserModel.last_activity_at.is_(None)
                    )
                )
            ).order_by(asc(UserModel.last_activity_at)).limit(limit).all()
            
            users = []
            for user_model in user_models:
                user = await self._model_to_domain(user_model)
                users.append(user)
            
            return users
            
        except SQLAlchemyError as e:
            logger.error("Find inactive users failed", days=days, error=str(e))
            raise DatabaseError(f"Failed to find inactive users: {str(e)}")
    
    async def find_expiring_trials(self, days: int = 3, limit: int = 100) -> List[User]:
        """
        Find users with trials expiring soon.
        
        Args:
            days: Number of days until expiration
            limit: Maximum number of results
            
        Returns:
            List[User]: List of users with expiring trials
        """
        try:
            session = await self._get_session()
            
            end_date = datetime.utcnow() + timedelta(days=days)
            
            user_models = await session.query(UserModel).options(
                selectinload(UserModel.subscription),
                selectinload(UserModel.profile)
            ).join(SubscriptionModel).filter(
                and_(
                    SubscriptionModel.status == SubscriptionStatus.TRIAL.value,
                    SubscriptionModel.trial_end_date <= end_date,
                    SubscriptionModel.trial_end_date >= datetime.utcnow()
                )
            ).order_by(asc(SubscriptionModel.trial_end_date)).limit(limit).all()
            
            users = []
            for user_model in user_models:
                user = await self._model_to_domain(user_model)
                users.append(user)
            
            return users
            
        except SQLAlchemyError as e:
            logger.error("Find expiring trials failed", days=days, error=str(e))
            raise DatabaseError(f"Failed to find expiring trials: {str(e)}")
    
    async def search_users(self, query: str, limit: int = 50, offset: int = 0) -> List[User]:
        """
        Search users by email or display name.
        
        Args:
            query: Search query
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[User]: List of matching users
        """
        try:
            session = await self._get_session()
            
            search_term = f"%{query}%"
            
            user_models = await session.query(UserModel).options(
                selectinload(UserModel.subscription),
                selectinload(UserModel.profile)
            ).join(ProfileModel).filter(
                or_(
                    UserModel.email.ilike(search_term),
                    ProfileModel.display_name.ilike(search_term)
                )
            ).offset(offset).limit(limit).all()
            
            users = []
            for user_model in user_models:
                user = await self._model_to_domain(user_model)
                users.append(user)
            
            return users
            
        except SQLAlchemyError as e:
            logger.error("Search users failed", query=query, error=str(e))
            raise DatabaseError(f"Failed to search users: {str(e)}")
    
    async def count_users_by_role(self, role: UserRole) -> int:
        """
        Count users by role.
        
        Args:
            role: User role to count
            
        Returns:
            int: Number of users with the specified role
        """
        try:
            session = await self._get_session()
            
            count = await session.query(func.count(UserModel.user_id)).filter(
                UserModel.role == role.value
            ).scalar()
            
            return count or 0
            
        except SQLAlchemyError as e:
            logger.error("Count users by role failed", role=role.value, error=str(e))
            raise DatabaseError(f"Failed to count users by role: {str(e)}")
    
    async def count_users_by_status(self, status: UserStatus) -> int:
        """
        Count users by status.
        
        Args:
            status: User status to count
            
        Returns:
            int: Number of users with the specified status
        """
        try:
            session = await self._get_session()
            
            count = await session.query(func.count(UserModel.user_id)).filter(
                UserModel.status == status.value
            ).scalar()
            
            return count or 0
            
        except SQLAlchemyError as e:
            logger.error("Count users by status failed", status=status.value, error=str(e))
            raise DatabaseError(f"Failed to count users by status: {str(e)}")
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive user statistics.
        
        Returns:
            Dict[str, Any]: User statistics
        """
        try:
            session = await self._get_session()
            
            # Total users
            total_users = await session.query(func.count(UserModel.user_id)).scalar()
            
            # Users by status
            status_counts = {}
            for status in UserStatus:
                count = await self.count_users_by_status(status)
                status_counts[status.value] = count
            
            # Users by role
            role_counts = {}
            for role in UserRole:
                count = await self.count_users_by_role(role)
                role_counts[role.value] = count
            
            # Subscription tier counts
            tier_counts = {}
            for tier in SubscriptionTier:
                count = await session.query(func.count(UserModel.user_id)).join(
                    SubscriptionModel
                ).filter(SubscriptionModel.tier == tier.value).scalar()
                tier_counts[tier.value] = count or 0
            
            # Recent registrations (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_registrations = await session.query(func.count(UserModel.user_id)).filter(
                UserModel.created_at >= thirty_days_ago
            ).scalar()
            
            # Active users (logged in last 30 days)
            active_users = await session.query(func.count(UserModel.user_id)).filter(
                and_(
                    UserModel.status == UserStatus.ACTIVE.value,
                    UserModel.last_login_at >= thirty_days_ago
                )
            ).scalar()
            
            return {
                "total_users": total_users or 0,
                "status_breakdown": status_counts,
                "role_breakdown": role_counts,
                "subscription_breakdown": tier_counts,
                "recent_registrations_30d": recent_registrations or 0,
                "active_users_30d": active_users or 0,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except SQLAlchemyError as e:
            logger.error("Get user stats failed", error=str(e))
            raise DatabaseError(f"Failed to get user statistics: {str(e)}")
    
    async def delete(self, user_id: str) -> bool:
        """
        Hard delete a user from the database.
        
        Args:
            user_id: User ID to delete
            
        Returns:
            bool: True if user was deleted, False if not found
            
        Raises:
            DatabaseError: If deletion fails
        """
        try:
            session = await self._get_session()
            
            logger.warning("Hard deleting user from database", user_id=user_id)
            
            user_model = await session.get(UserModel, user_id)
            if not user_model:
                return False
            
            await session.delete(user_model)
            await session.commit()
            
            logger.warning("User hard deleted from database", user_id=user_id)
            
            return True
            
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("User deletion failed", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to delete user: {str(e)}")
    
    # Private helper methods
    
    async def _model_to_domain(self, user_model: UserModel) -> User:
        """Convert database model to domain model."""
        # Convert subscription if exists
        subscription = None
        if user_model.subscription:
            sub_model = user_model.subscription
            subscription = Subscription(
                subscription_id=sub_model.subscription_id,
                user_id=sub_model.user_id,
                tier=SubscriptionTier(sub_model.tier),
                status=SubscriptionStatus(sub_model.status),
                billing_cycle=BillingCycle(sub_model.billing_cycle) if sub_model.billing_cycle else None,
                price=sub_model.price,
                currency=sub_model.currency,
                trial_end_date=sub_model.trial_end_date,
                current_period_start=sub_model.current_period_start,
                current_period_end=sub_model.current_period_end,
                next_billing_date=sub_model.next_billing_date,
                payment_method_id=sub_model.payment_method_id,
                last_payment_date=sub_model.last_payment_date,
                last_payment_amount=sub_model.last_payment_amount,
                cancel_at_period_end=sub_model.cancel_at_period_end,
                cancelled_at=sub_model.cancelled_at,
                cancellation_reason=sub_model.cancellation_reason,
                created_at=sub_model.created_at,
                updated_at=sub_model.updated_at
            )
        
        # Create domain user
        user = User(
            user_id=user_model.user_id,
            email=user_model.email,
            supabase_user_id=user_model.supabase_user_id,
            password_hash=user_model.password_hash,
            provider=user_model.provider,
            role=UserRole(user_model.role),
            status=UserStatus(user_model.status),
            is_verified=user_model.is_verified,
            is_onboarded=user_model.is_onboarded,
            plant_limit=user_model.plant_limit,
            subscription=subscription,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
            last_login_at=user_model.last_login_at,
            last_activity_at=user_model.last_activity_at,
            email_verified_at=user_model.email_verified_at,
            onboarded_at=user_model.onboarded_at,
            deleted_at=user_model.deleted_at,
            deletion_reason=user_model.deletion_reason
        )
        
        # Add additional attributes
        user.failed_login_attempts = user_model.failed_login_attempts
        user.locked_until = user_model.locked_until
        
        return user


# Factory function for dependency injection
def create_postgresql_user_repository(session: Optional[Session] = None) -> PostgreSQLUserRepository:
    """Create PostgreSQL user repository instance."""
    return PostgreSQLUserRepository(session)