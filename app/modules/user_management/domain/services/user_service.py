# app/modules/user_management/domain/services/user_service.py
"""
Plant Care Application - User Domain Service

Core user management business logic for the Plant Care Application.
Handles user lifecycle, plant count management, and premium feature access.
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

import structlog

from app.modules.user_management.domain.models.user import User, UserRole, UserStatus
from app.modules.user_management.domain.models.profile import Profile
from app.modules.user_management.domain.models.subscription import Subscription, SubscriptionTier
from app.modules.user_management.domain.repositories.user_repository import UserRepository
from app.modules.user_management.domain.repositories.profile_repository import ProfileRepository
from app.modules.user_management.domain.events.user_events import (
    UserRegistered, UserActivated, UserDeactivated, UserSuspended,
    UserEmailVerified, UserRoleChanged, UserUpgradedToPremium,
    UserDowngradedFromPremium, UserPromotedToExpert, UserPlantCountUpdated
)
from app.shared.events.base import EventPublisher
from app.shared.core.exceptions import (
    ValidationError, BusinessLogicError, ResourceNotFoundError,
    AuthorizationError, ResourceAlreadyExistsError
)

# Setup logger
logger = structlog.get_logger(__name__)


class UserService:
    """
    Domain service for user management in Plant Care Application.
    Handles core user operations, business rules, and plant count management.
    """
    
    def __init__(self, 
                 user_repository: UserRepository,
                 profile_repository: ProfileRepository,
                 event_publisher: EventPublisher):
        """
        Initialize user service.
        
        Args:
            user_repository: User data repository
            profile_repository: Profile data repository  
            event_publisher: Event publisher for domain events
        """
        self.user_repository = user_repository
        self.profile_repository = profile_repository
        self.event_publisher = event_publisher
    
    async def register_user(self, 
                           email: str,
                           supabase_user_id: Optional[str] = None,
                           registration_source: str = "web") -> User:
        """
        Register a new user in the Plant Care Application.
        
        Args:
            email: User email address
            supabase_user_id: Supabase user ID if available
            registration_source: Source of registration (web, mobile, api)
            
        Returns:
            User: Newly created user
            
        Raises:
            ValidationError: If email is invalid
            ResourceAlreadyExistsError: If user already exists
            BusinessLogicError: If registration fails business rules
        """
        try:
            logger.info("Starting user registration", email=email, source=registration_source)
            
            # Business rule: Check if user already exists
            existing_user = await self.user_repository.find_by_email(email)
            if existing_user:
                raise ResourceAlreadyExistsError("User", email)
            
            # Business rule: Validate email format
            if not self._is_valid_email(email):
                raise ValidationError("Invalid email format")
            
            # Create new user with Plant Care defaults
            user = User(
                email=email,
                supabase_user_id=supabase_user_id,
                role=UserRole.USER,
                status=UserStatus.PENDING,  # Requires email verification
                subscription_tier="free",
                is_premium=False,
                plant_count=0,
                metadata={
                    "registration_source": registration_source,
                    "registration_ip": None,  # To be set by infrastructure layer
                    "terms_accepted": True,
                    "marketing_consent": False,
                }
            )
            
            # Save user
            saved_user = await self.user_repository.save(user)
            
            # Publish domain event
            event = UserRegistered(
                user_id=saved_user.user_id,
                email=saved_user.email,
                supabase_user_id=supabase_user_id,
                registration_source=registration_source
            )
            await self.event_publisher.publish(event)
            
            logger.info("User registered successfully", 
                       user_id=saved_user.user_id, 
                       email=email)
            
            return saved_user
            
        except Exception as e:
            logger.error("User registration failed", email=email, error=str(e))
            raise
    
    async def activate_user(self, user_id: str, activation_method: str = "email_verification") -> User:
        """
        Activate a user account.
        
        Args:
            user_id: ID of user to activate
            activation_method: Method used for activation
            
        Returns:
            User: Activated user
            
        Raises:
            ResourceNotFoundError: If user not found
            BusinessLogicError: If user cannot be activated
        """
        try:
            logger.info("Activating user", user_id=user_id, method=activation_method)
            
            # Get user
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", user_id)
            
            # Business rule: User must be verified before activation
            if activation_method == "email_verification" and not user.email_verified:
                raise BusinessLogicError("Cannot activate user without email verification")
            
            # Activate user
            user.activate()
            
            # Save user
            saved_user = await self.user_repository.save(user)
            
            # Publish domain event
            event = UserActivated(
                user_id=saved_user.user_id,
                email=saved_user.email,
                activation_method=activation_method
            )
            await self.event_publisher.publish(event)
            
            logger.info("User activated successfully", user_id=user_id)
            
            return saved_user
            
        except Exception as e:
            logger.error("User activation failed", user_id=user_id, error=str(e))
            raise
    
    async def verify_email(self, user_id: str, verification_method: str = "email_link") -> User:
        """
        Verify user email address.
        
        Args:
            user_id: ID of user to verify
            verification_method: Method used for verification
            
        Returns:
            User: User with verified email
            
        Raises:
            ResourceNotFoundError: If user not found
        """
        try:
            logger.info("Verifying user email", user_id=user_id, method=verification_method)
            
            # Get user
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", user_id)
            
            # Verify email
            user.verify_email()
            
            # Save user
            saved_user = await self.user_repository.save(user)
            
            # Publish domain event
            event = UserEmailVerified(
                user_id=saved_user.user_id,
                email=saved_user.email,
                verification_method=verification_method
            )
            await self.event_publisher.publish(event)
            
            logger.info("User email verified successfully", user_id=user_id)
            
            return saved_user
            
        except Exception as e:
            logger.error("Email verification failed", user_id=user_id, error=str(e))
            raise
    
    async def deactivate_user(self, user_id: str, reason: Optional[str] = None,
                             deactivated_by: Optional[str] = None) -> User:
        """
        Deactivate a user account.
        
        Args:
            user_id: ID of user to deactivate
            reason: Reason for deactivation
            deactivated_by: ID of admin who deactivated (if applicable)
            
        Returns:
            User: Deactivated user
            
        Raises:
            ResourceNotFoundError: If user not found
        """
        try:
            logger.info("Deactivating user", user_id=user_id, reason=reason)
            
            # Get user
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", user_id)
            
            # Deactivate user
            user.deactivate(reason)
            
            # Save user
            saved_user = await self.user_repository.save(user)
            
            # Publish domain event
            event = UserDeactivated(
                user_id=saved_user.user_id,
                email=saved_user.email,
                reason=reason,
                deactivated_by=deactivated_by
            )
            await self.event_publisher.publish(event)
            
            logger.info("User deactivated successfully", user_id=user_id)
            
            return saved_user
            
        except Exception as e:
            logger.error("User deactivation failed", user_id=user_id, error=str(e))
            raise
    
    async def suspend_user(self, user_id: str, reason: str, 
                          suspended_by: str, suspended_until: Optional[datetime] = None) -> User:
        """
        Suspend a user account.
        
        Args:
            user_id: ID of user to suspend
            reason: Reason for suspension
            suspended_by: ID of admin who suspended
            suspended_until: Optional end date for suspension
            
        Returns:
            User: Suspended user
            
        Raises:
            ResourceNotFoundError: If user not found
            ValidationError: If reason is empty
        """
        try:
            logger.info("Suspending user", user_id=user_id, reason=reason)
            
            # Get user
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", user_id)
            
            # Suspend user
            user.suspend(reason, suspended_until)
            
            # Save user
            saved_user = await self.user_repository.save(user)
            
            # Publish domain event
            event = UserSuspended(
                user_id=saved_user.user_id,
                email=saved_user.email,
                reason=reason,
                suspended_by=suspended_by,
                suspended_until=suspended_until
            )
            await self.event_publisher.publish(event)
            
            logger.warning("User suspended", user_id=user_id, reason=reason)
            
            return saved_user
            
        except Exception as e:
            logger.error("User suspension failed", user_id=user_id, error=str(e))
            raise
    
    async def upgrade_to_premium(self, user_id: str, subscription_tier: str = "premium",
                                upgrade_source: str = "manual") -> User:
        """
        Upgrade user to premium tier.
        
        Args:
            user_id: ID of user to upgrade
            subscription_tier: Premium tier to upgrade to
            upgrade_source: Source of upgrade (manual, trial_conversion, admin)
            
        Returns:
            User: Upgraded user
            
        Raises:
            ResourceNotFoundError: If user not found
            BusinessLogicError: If user cannot be upgraded
        """
        try:
            logger.info("Upgrading user to premium", user_id=user_id, tier=subscription_tier)
            
            # Get user
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", user_id)
            
            # Business rule: User must be active to upgrade
            if not user.is_active():
                raise BusinessLogicError("Cannot upgrade inactive user to premium")
            
            # Upgrade user
            user.upgrade_to_premium()
            user.subscription_tier = subscription_tier
            
            # Save user
            saved_user = await self.user_repository.save(user)
            
            # Publish domain event
            event = UserUpgradedToPremium(
                user_id=saved_user.user_id,
                email=saved_user.email,
                subscription_tier=subscription_tier,
                upgrade_source=upgrade_source
            )
            await self.event_publisher.publish(event)
            
            logger.info("User upgraded to premium successfully", user_id=user_id)
            
            return saved_user
            
        except Exception as e:
            logger.error("Premium upgrade failed", user_id=user_id, error=str(e))
            raise
    
    async def downgrade_from_premium(self, user_id: str, new_tier: str = "free",
                                   downgrade_reason: str = "subscription_ended") -> User:
        """
        Downgrade user from premium tier.
        
        Args:
            user_id: ID of user to downgrade
            new_tier: New tier after downgrade
            downgrade_reason: Reason for downgrade
            
        Returns:
            User: Downgraded user
            
        Raises:
            ResourceNotFoundError: If user not found
            BusinessLogicError: If plant count exceeds free tier limits
        """
        try:
            logger.info("Downgrading user from premium", user_id=user_id, new_tier=new_tier)
            
            # Get user
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", user_id)
            
            old_tier = user.subscription_tier
            
            # Business rule: Check plant count limits for free tier
            if new_tier == "free" and user.plant_count > 5:
                raise BusinessLogicError(
                    f"Cannot downgrade to free tier: user has {user.plant_count} plants (limit: 5). "
                    "Please reduce plant count or keep premium subscription."
                )
            
            # Downgrade user
            user.downgrade_from_premium()
            user.subscription_tier = new_tier
            
            # Save user
            saved_user = await self.user_repository.save(user)
            
            # Publish domain event
            event = UserDowngradedFromPremium(
                user_id=saved_user.user_id,
                email=saved_user.email,
                old_tier=old_tier,
                new_tier=new_tier,
                downgrade_reason=downgrade_reason
            )
            await self.event_publisher.publish(event)
            
            logger.info("User downgraded from premium successfully", user_id=user_id)
            
            return saved_user
            
        except Exception as e:
            logger.error("Premium downgrade failed", user_id=user_id, error=str(e))
            raise
    
    async def promote_to_expert(self, user_id: str, promoted_by: str,
                               expert_specialties: List[str] = None) -> User:
        """
        Promote user to expert role.
        
        Args:
            user_id: ID of user to promote
            promoted_by: ID of admin who promoted
            expert_specialties: List of expert specialties
            
        Returns:
            User: Promoted user
            
        Raises:
            ResourceNotFoundError: If user not found
            BusinessLogicError: If user cannot be promoted
        """
        try:
            logger.info("Promoting user to expert", user_id=user_id, specialties=expert_specialties)
            
            # Get user
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", user_id)
            
            old_role = user.role
            
            # Promote user
            user.promote_to_expert()
            
            # Save user
            saved_user = await self.user_repository.save(user)
            
            # Publish domain events
            role_event = UserRoleChanged(
                user_id=saved_user.user_id,
                email=saved_user.email,
                old_role=old_role.value,
                new_role=saved_user.role.value,
                changed_by=promoted_by
            )
            await self.event_publisher.publish(role_event)
            
            expert_event = UserPromotedToExpert(
                user_id=saved_user.user_id,
                email=saved_user.email,
                promoted_by=promoted_by,
                expert_specialties=expert_specialties or []
            )
            await self.event_publisher.publish(expert_event)
            
            logger.info("User promoted to expert successfully", user_id=user_id)
            
            return saved_user
            
        except Exception as e:
            logger.error("Expert promotion failed", user_id=user_id, error=str(e))
            raise
    
    async def update_plant_count(self, user_id: str, new_count: int,
                               change_reason: str = "plant_added") -> User:
        """
        Update user's plant count with business rule validation.
        
        Args:
            user_id: ID of user to update
            new_count: New plant count
            change_reason: Reason for change
            
        Returns:
            User: Updated user
            
        Raises:
            ResourceNotFoundError: If user not found
            BusinessLogicError: If plant count violates tier limits
        """
        try:
            logger.info("Updating plant count", user_id=user_id, new_count=new_count)
            
            # Get user
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", user_id)
            
            old_count = user.plant_count
            
            # Update plant count (includes business rule validation)
            user.update_plant_count(new_count)
            
            # Save user
            saved_user = await self.user_repository.save(user)
            
            # Publish domain event
            event = UserPlantCountUpdated(
                user_id=saved_user.user_id,
                old_count=old_count,
                new_count=new_count,
                change_reason=change_reason
            )
            await self.event_publisher.publish(event)
            
            logger.info("Plant count updated successfully", 
                       user_id=user_id, 
                       old_count=old_count, 
                       new_count=new_count)
            
            return saved_user
            
        except Exception as e:
            logger.error("Plant count update failed", user_id=user_id, error=str(e))
            raise
    
    async def can_add_plant(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user can add another plant.
        
        Args:
            user_id: ID of user to check
            
        Returns:
            Tuple[bool, Optional[str]]: (can_add, reason_if_not)
            
        Raises:
            ResourceNotFoundError: If user not found
        """
        try:
            # Get user
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", user_id)
            
            # Check if user can add plant
            can_add = user.can_add_plant()
            
            if not can_add:
                remaining_slots = user.get_remaining_plant_slots()
                if remaining_slots == 0:
                    reason = "Free tier limited to 5 plants. Upgrade to premium for unlimited plants."
                else:
                    reason = f"Free tier limit reached: {user.plant_count}/5 plants used."
                return False, reason
            
            return True, None
            
        except Exception as e:
            logger.error("Plant addition check failed", user_id=user_id, error=str(e))
            raise
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive user statistics for Plant Care Application.
        
        Args:
            user_id: ID of user
            
        Returns:
            Dict[str, Any]: User statistics
            
        Raises:
            ResourceNotFoundError: If user not found
        """
        try:
            # Get user and profile
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError("User", user_id)
            
            profile = await self.profile_repository.find_by_user_id(user_id)
            
            # Calculate statistics
            account_age_days = (datetime.utcnow() - user.created_at).days
            remaining_plant_slots = user.get_remaining_plant_slots()
            
            statistics = {
                "user_info": {
                    "user_id": user.user_id,
                    "email": user.email,
                    "role": user.role.value,
                    "status": user.status.value,
                    "is_premium": user.is_premium,
                    "subscription_tier": user.subscription_tier,
                    "email_verified": user.email_verified,
                },
                "plant_statistics": {
                    "plant_count": user.plant_count,
                    "remaining_slots": remaining_plant_slots,
                    "can_add_plant": user.can_add_plant(),
                },
                "account_statistics": {
                    "account_age_days": account_age_days,
                    "last_login": user.last_login_at.isoformat() if user.last_login_at else None,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                },
                "profile_info": {
                    "has_profile": profile is not None,
                    "display_name": profile.get_display_name() if profile else None,
                    "experience_level": profile.experience_level if profile else None,
                    "is_verified_expert": profile.is_verified_expert if profile else False,
                    "expert_rating": profile.expert_rating if profile else None,
                } if profile else {
                    "has_profile": False,
                    "display_name": None,
                    "experience_level": None,
                    "is_verified_expert": False,
                    "expert_rating": None,
                }
            }
            
            return statistics
            
        except Exception as e:
            logger.error("Failed to get user statistics", user_id=user_id, error=str(e))
            raise
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Basic email validation
        if not email or "@" not in email:
            return False
        
        parts = email.split("@")
        if len(parts) != 2:
            return False
        
        local, domain = parts
        if not local or not domain or "." not in domain:
            return False
        
        return True