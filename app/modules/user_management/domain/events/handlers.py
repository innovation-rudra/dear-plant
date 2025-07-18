# app/modules/user_management/domain/events/handlers.py
"""
Plant Care Application - User Management Domain Event Handlers

Event handlers for user management domain events.
These handlers contain business logic that should execute when domain events occur.
They maintain consistency within the user management domain.
"""

from typing import Dict, Any
import structlog

from app.shared.events.base import BaseEvent, EventHandler
from app.modules.user_management.domain.events.user_events import (
    UserRegistered,
    UserActivated,
    UserDeactivated,
    UserSuspended,
    UserEmailVerified,
    UserRoleChanged,
    UserLastLoginUpdated,
    UserUpgradedToPremium,
    UserDowngradedFromPremium,
    UserPromotedToExpert,
    UserPlantCountUpdated,
    ProfileCreated,
    ProfileUpdated,
    ProfileAvatarUpdated,
    ProfileExperienceLevelUpdated,
    ProfileVerifiedAsExpert,
    SubscriptionCreated,
    SubscriptionUpgraded,
    SubscriptionDowngraded,
    SubscriptionCancelled,
    SubscriptionReactivated,
    SubscriptionTrialStarted,
    SubscriptionTrialEnded,
    SubscriptionPaymentRecorded,
    SubscriptionPaymentFailed,
    SubscriptionExpired,
)

# Setup logger
logger = structlog.get_logger(__name__)


class UserRegistrationHandler(EventHandler):
    """
    Handles user registration events.
    Ensures proper setup of user account and related entities.
    """
    
    def can_handle(self, event: BaseEvent) -> bool:
        """Check if this handler can process the event."""
        return isinstance(event, UserRegistered)
    
    async def handle(self, event: UserRegistered) -> None:
        """
        Handle user registration event.
        
        Args:
            event: User registration event
        """
        try:
            logger.info("Processing user registration", 
                       user_id=event.user_id, 
                       email=event.email,
                       source=event.registration_source)
            
            # Business logic for user registration
            # Note: Actual implementation will be in application layer
            # This is just the domain event handler
            
            # Domain rules:
            # 1. User should start with free tier
            # 2. Default profile should be created
            # 3. Welcome sequence should be initiated
            
            # Log successful processing
            logger.info("User registration processed successfully", 
                       user_id=event.user_id)
            
        except Exception as e:
            logger.error("Failed to process user registration", 
                        user_id=event.user_id, 
                        error=str(e))
            raise


class UserActivationHandler(EventHandler):
    """
    Handles user activation events.
    Manages post-activation setup and notifications.
    """
    
    def can_handle(self, event: BaseEvent) -> bool:
        """Check if this handler can process the event."""
        return isinstance(event, (UserActivated, UserEmailVerified))
    
    async def handle(self, event: BaseEvent) -> None:
        """
        Handle user activation event.
        
        Args:
            event: User activation or email verification event
        """
        try:
            if isinstance(event, UserActivated):
                logger.info("Processing user activation", 
                           user_id=event.user_id,
                           method=event.activation_method)
            elif isinstance(event, UserEmailVerified):
                logger.info("Processing email verification", 
                           user_id=event.user_id,
                           method=event.verification_method)
            
            # Business logic for user activation
            # Domain rules:
            # 1. Send welcome email with Plant Care tips
            # 2. Create default plant care preferences
            # 3. Setup initial notifications
            # 4. Enable plant addition capabilities
            
            logger.info("User activation processed successfully", 
                       user_id=event.user_id)
            
        except Exception as e:
            logger.error("Failed to process user activation", 
                        user_id=event.user_id, 
                        error=str(e))
            raise


class UserStatusHandler(EventHandler):
    """
    Handles user status change events.
    Manages user deactivation and suspension logic.
    """
    
    def can_handle(self, event: BaseEvent) -> bool:
        """Check if this handler can process the event."""
        return isinstance(event, (UserDeactivated, UserSuspended))
    
    async def handle(self, event: BaseEvent) -> None:
        """
        Handle user status change event.
        
        Args:
            event: User status change event
        """
        try:
            if isinstance(event, UserDeactivated):
                await self._handle_user_deactivated(event)
            elif isinstance(event, UserSuspended):
                await self._handle_user_suspended(event)
            
        except Exception as e:
            logger.error("Failed to process user status change", 
                        user_id=getattr(event, 'user_id', 'unknown'),
                        error=str(e))
            raise
    
    async def _handle_user_deactivated(self, event: UserDeactivated) -> None:
        """Handle user deactivation."""
        logger.info("Processing user deactivation", 
                   user_id=event.user_id,
                   reason=event.reason)
        
        # Business logic for user deactivation
        # Domain rules:
        # 1. Disable all notifications
        # 2. Hide profile from public view
        # 3. Pause care reminders
        # 4. Maintain plant data for potential reactivation
    
    async def _handle_user_suspended(self, event: UserSuspended) -> None:
        """Handle user suspension."""
        logger.warning("Processing user suspension", 
                      user_id=event.user_id,
                      reason=event.reason,
                      suspended_by=event.suspended_by)
        
        # Business logic for user suspension
        # Domain rules:
        # 1. Immediately disable account access
        # 2. Send suspension notification
        # 3. Hide all user content
        # 4. Log security event


class SubscriptionHandler(EventHandler):
    """
    Handles subscription-related events.
    Manages subscription lifecycle and feature access.
    """
    
    def can_handle(self, event: BaseEvent) -> bool:
        """Check if this handler can process the event."""
        return isinstance(event, (
            SubscriptionCreated,
            SubscriptionUpgraded, 
            SubscriptionDowngraded,
            SubscriptionCancelled,
            SubscriptionReactivated,
            SubscriptionExpired,
            SubscriptionTrialStarted,
            SubscriptionTrialEnded,
            SubscriptionPaymentRecorded,
            SubscriptionPaymentFailed,
            UserUpgradedToPremium,
            UserDowngradedFromPremium,
        ))
    
    async def handle(self, event: BaseEvent) -> None:
        """
        Handle subscription event.
        
        Args:
            event: Subscription-related event
        """
        try:
            if isinstance(event, SubscriptionCreated):
                await self._handle_subscription_created(event)
            elif isinstance(event, SubscriptionUpgraded):
                await self._handle_subscription_upgraded(event)
            elif isinstance(event, SubscriptionDowngraded):
                await self._handle_subscription_downgraded(event)
            elif isinstance(event, UserUpgradedToPremium):
                await self._handle_user_upgraded_to_premium(event)
            elif isinstance(event, UserDowngradedFromPremium):
                await self._handle_user_downgraded_from_premium(event)
            elif isinstance(event, SubscriptionCancelled):
                await self._handle_subscription_cancelled(event)
            elif isinstance(event, SubscriptionReactivated):
                await self._handle_subscription_reactivated(event)
            elif isinstance(event, SubscriptionExpired):
                await self._handle_subscription_expired(event)
            elif isinstance(event, SubscriptionTrialStarted):
                await self._handle_trial_started(event)
            elif isinstance(event, SubscriptionTrialEnded):
                await self._handle_trial_ended(event)
            elif isinstance(event, SubscriptionPaymentRecorded):
                await self._handle_payment_recorded(event)
            elif isinstance(event, SubscriptionPaymentFailed):
                await self._handle_payment_failed(event)
            
        except Exception as e:
            logger.error("Failed to process subscription event", 
                        event_type=event.event_type,
                        error=str(e))
            raise
    
    async def _handle_subscription_created(self, event: SubscriptionCreated) -> None:
        """Handle subscription creation."""
        logger.info("Processing subscription creation", 
                   subscription_id=event.subscription_id,
                   user_id=event.user_id,
                   tier=event.tier)
        
        # Business logic for subscription creation
        # Domain rules:
        # 1. Update user premium status
        # 2. Send confirmation email
        # 3. Setup billing notifications
        # 4. Enable tier-specific features
    
    async def _handle_subscription_upgraded(self, event: SubscriptionUpgraded) -> None:
        """Handle subscription upgrade."""
        logger.info("Processing subscription upgrade", 
                   subscription_id=event.subscription_id,
                   old_tier=event.old_tier,
                   new_tier=event.new_tier)
        
        # Business logic for subscription upgrade
        # Domain rules:
        # 1. Unlock premium features immediately
        # 2. Send upgrade confirmation
        # 3. Update plant limits if applicable
        # 4. Enable advanced analytics
    
    async def _handle_subscription_downgraded(self, event: SubscriptionDowngraded) -> None:
        """Handle subscription downgrade."""
        logger.info("Processing subscription downgrade", 
                   subscription_id=event.subscription_id,
                   old_tier=event.old_tier,
                   new_tier=event.new_tier,
                   reason=event.reason)
        
        # Business logic for subscription downgrade
        # Domain rules:
        # 1. Disable premium features
        # 2. Check plant count limits
        # 3. Send downgrade notification
        # 4. Maintain grace period for data access
    
    async def _handle_user_upgraded_to_premium(self, event: UserUpgradedToPremium) -> None:
        """Handle user premium upgrade."""
        logger.info("Processing user premium upgrade", 
                   user_id=event.user_id,
                   tier=event.subscription_tier,
                   source=event.upgrade_source)
        
        # Business logic for premium upgrade
        # Domain rules:
        # 1. Enable premium Plant Care features
        # 2. Remove plant count restrictions
        # 3. Enable AI plant identification
        # 4. Send welcome to premium email
        # 5. Update user role and permissions
    
    async def _handle_user_downgraded_from_premium(self, event: UserDowngradedFromPremium) -> None:
        """Handle user premium downgrade."""
        logger.info("Processing user premium downgrade", 
                   user_id=event.user_id,
                   old_tier=event.old_tier,
                   new_tier=event.new_tier,
                   reason=event.downgrade_reason)
        
        # Business logic for premium downgrade
        # Domain rules:
        # 1. Check plant count limits for free tier (max 5 plants)
        # 2. Disable premium features
        # 3. Send downgrade notification
        # 4. Archive excess plants if needed
        # 5. Maintain basic plant care features
    
    async def _handle_subscription_cancelled(self, event: SubscriptionCancelled) -> None:
        """Handle subscription cancellation."""
        logger.info("Processing subscription cancellation", 
                   subscription_id=event.subscription_id,
                   reason=event.cancellation_reason,
                   immediate=event.immediate,
                   cancelled_by=event.cancelled_by)
        
        # Business logic for cancellation
        # Domain rules:
        # 1. Send cancellation confirmation
        # 2. Schedule feature downgrade if not immediate
        # 3. Collect feedback if applicable
        # 4. Offer retention incentives
    
    async def _handle_subscription_reactivated(self, event: SubscriptionReactivated) -> None:
        """Handle subscription reactivation."""
        logger.info("Processing subscription reactivation", 
                   subscription_id=event.subscription_id,
                   tier=event.tier,
                   reason=event.reactivation_reason)
        
        # Business logic for reactivation
        # Domain rules:
        # 1. Restore premium features
        # 2. Send reactivation welcome
        # 3. Update billing cycle
        # 4. Re-enable notifications
    
    async def _handle_subscription_expired(self, event: SubscriptionExpired) -> None:
        """Handle subscription expiration."""
        logger.info("Processing subscription expiration", 
                   subscription_id=event.subscription_id,
                   expired_tier=event.expired_tier,
                   reason=event.expiration_reason)
        
        # Business logic for expiration
        # Domain rules:
        # 1. Downgrade to free tier immediately
        # 2. Send expiration notification
        # 3. Offer reactivation options
        # 4. Apply free tier plant limits
    
    async def _handle_trial_started(self, event: SubscriptionTrialStarted) -> None:
        """Handle trial start."""
        logger.info("Processing trial start", 
                   subscription_id=event.subscription_id,
                   tier=event.tier,
                   trial_days=event.trial_days)
        
        # Business logic for trial start
        # Domain rules:
        # 1. Enable premium features temporarily
        # 2. Send trial welcome email
        # 3. Setup trial reminder notifications
        # 4. Track trial usage
    
    async def _handle_trial_ended(self, event: SubscriptionTrialEnded) -> None:
        """Handle trial end."""
        logger.info("Processing trial end", 
                   subscription_id=event.subscription_id,
                   converted=event.converted_to_paid)
        
        # Business logic for trial end
        if event.converted_to_paid:
            # Domain rules for conversion:
            # 1. Send welcome to paid subscription
            # 2. Continue premium features
            # 3. Setup billing cycle
            pass
        else:
            # Domain rules for trial expiration:
            # 1. Send trial ended notification
            # 2. Offer conversion incentives
            # 3. Downgrade to free tier
            # 4. Apply free tier limitations
            pass
    
    async def _handle_payment_recorded(self, event: SubscriptionPaymentRecorded) -> None:
        """Handle successful payment."""
        logger.info("Processing payment success", 
                   subscription_id=event.subscription_id,
                   amount=event.amount,
                   currency=event.currency)
        
        # Business logic for successful payment
        # Domain rules:
        # 1. Send payment confirmation
        # 2. Extend subscription period
        # 3. Clear any payment failure flags
        # 4. Update billing history
    
    async def _handle_payment_failed(self, event: SubscriptionPaymentFailed) -> None:
        """Handle payment failure."""
        logger.warning("Processing payment failure", 
                      subscription_id=event.subscription_id,
                      retry_count=event.retry_count,
                      reason=event.failure_reason)
        
        # Business logic for payment failure
        # Domain rules:
        # 1. Send payment failure notification
        # 2. Update payment method if needed
        # 3. Schedule retry or account suspension
        # 4. Provide grace period for free users


class ProfileHandler(EventHandler):
    """
    Handles profile-related events.
    Manages profile updates and expert verification.
    """
    
    def can_handle(self, event: BaseEvent) -> bool:
        """Check if this handler can process the event."""
        return isinstance(event, (
            ProfileCreated,
            ProfileUpdated,
            ProfileAvatarUpdated,
            ProfileExperienceLevelUpdated,
            ProfileVerifiedAsExpert,
            UserPromotedToExpert,
        ))
    
    async def handle(self, event: BaseEvent) -> None:
        """
        Handle profile event.
        
        Args:
            event: Profile-related event
        """
        try:
            if isinstance(event, ProfileCreated):
                await self._handle_profile_created(event)
            elif isinstance(event, ProfileUpdated):
                await self._handle_profile_updated(event)
            elif isinstance(event, ProfileAvatarUpdated):
                await self._handle_avatar_updated(event)
            elif isinstance(event, ProfileExperienceLevelUpdated):
                await self._handle_experience_updated(event)
            elif isinstance(event, ProfileVerifiedAsExpert):
                await self._handle_expert_verification(event)
            elif isinstance(event, UserPromotedToExpert):
                await self._handle_expert_promotion(event)
            
        except Exception as e:
            logger.error("Failed to process profile event", 
                        event_type=event.event_type,
                        error=str(e))
            raise
    
    async def _handle_profile_created(self, event: ProfileCreated) -> None:
        """Handle profile creation."""
        logger.info("Processing profile creation", 
                   profile_id=event.profile_id,
                   user_id=event.user_id,
                   experience_level=event.experience_level)
        
        # Business logic for profile creation
        # Domain rules:
        # 1. Send profile setup reminder
        # 2. Create default Plant Care preferences
        # 3. Setup notification settings
        # 4. Encourage profile completion
    
    async def _handle_profile_updated(self, event: ProfileUpdated) -> None:
        """Handle profile update."""
        logger.info("Processing profile update", 
                   profile_id=event.profile_id,
                   user_id=event.user_id,
                   updated_fields=event.updated_fields)
        
        # Business logic for profile update
        # Domain rules:
        # 1. Validate profile completeness
        # 2. Update search indices if public
        # 3. Trigger recommendations refresh
    
    async def _handle_avatar_updated(self, event: ProfileAvatarUpdated) -> None:
        """Handle avatar update."""
        logger.info("Processing avatar update", 
                   profile_id=event.profile_id,
                   user_id=event.user_id)
        
        # Business logic for avatar update
        # Domain rules:
        # 1. Process image for different sizes
        # 2. Update profile completion status
        # 3. Clean up old avatar if needed
    
    async def _handle_experience_updated(self, event: ProfileExperienceLevelUpdated) -> None:
        """Handle experience level update."""
        logger.info("Processing experience level update", 
                   profile_id=event.profile_id,
                   old_level=event.old_level,
                   new_level=event.new_level)
        
        # Business logic for experience update
        # Domain rules:
        # 1. Adjust care recommendations
        # 2. Update expert eligibility
        # 3. Modify community privileges
    
    async def _handle_expert_verification(self, event: ProfileVerifiedAsExpert) -> None:
        """Handle expert verification."""
        logger.info("Processing expert verification", 
                   profile_id=event.profile_id,
                   user_id=event.user_id,
                   rating=event.expert_rating,
                   specialties=event.specialties)
        
        # Business logic for expert verification
        # Domain rules:
        # 1. Send expert verification notification
        # 2. Enable expert features in Plant Care
        # 3. Add to expert directory
        # 4. Setup consultation availability
        # 5. Grant expert permissions
    
    async def _handle_expert_promotion(self, event: UserPromotedToExpert) -> None:
        """Handle expert promotion."""
        logger.info("Processing expert promotion", 
                   user_id=event.user_id,
                   promoted_by=event.promoted_by,
                   specialties=event.expert_specialties)
        
        # Business logic for expert promotion
        # Domain rules:
        # 1. Update user permissions for Plant Care
        # 2. Send expert welcome package
        # 3. Setup expert consultation features
        # 4. Enable community moderation rights


class UserActivityHandler(EventHandler):
    """
    Handles user activity events.
    Manages login tracking and plant count updates.
    """
    
    def can_handle(self, event: BaseEvent) -> bool:
        """Check if this handler can process the event."""
        return isinstance(event, (
            UserLastLoginUpdated,
            UserPlantCountUpdated,
            UserRoleChanged,
        ))
    
    async def handle(self, event: BaseEvent) -> None:
        """
        Handle user activity event.
        
        Args:
            event: User activity event
        """
        try:
            if isinstance(event, UserLastLoginUpdated):
                await self._handle_login_updated(event)
            elif isinstance(event, UserPlantCountUpdated):
                await self._handle_plant_count_updated(event)
            elif isinstance(event, UserRoleChanged):
                await self._handle_role_changed(event)
            
        except Exception as e:
            logger.error("Failed to process user activity event", 
                        event_type=event.event_type,
                        error=str(e))
            raise
    
    async def _handle_login_updated(self, event: UserLastLoginUpdated) -> None:
        """Handle login update."""
        logger.info("Processing login update", 
                   user_id=event.user_id,
                   login_source=event.login_source)
        
        # Business logic for login update
        # Domain rules:
        # 1. Update user activity status
        # 2. Track login patterns for security
        # 3. Trigger engagement notifications if needed
    
    async def _handle_plant_count_updated(self, event: UserPlantCountUpdated) -> None:
        """Handle plant count update."""
        logger.info("Processing plant count update", 
                   user_id=event.user_id,
                   old_count=event.old_count,
                   new_count=event.new_count,
                   reason=event.change_reason)
        
        # Business logic for plant count update
        # Domain rules:
        # 1. Validate free tier limits (max 5 plants)
        # 2. Send upgrade suggestions if at limit
        # 3. Update user engagement level
        # 4. Trigger achievement notifications
    
    async def _handle_role_changed(self, event: UserRoleChanged) -> None:
        """Handle role change."""
        logger.info("Processing role change", 
                   user_id=event.user_id,
                   old_role=event.old_role,
                   new_role=event.new_role,
                   changed_by=event.changed_by)
        
        # Business logic for role change
        # Domain rules:
        # 1. Update user permissions
        # 2. Send role change notification
        # 3. Enable/disable features based on new role
        # 4. Log security event for auditing


class UserManagementEventHandlerRegistry:
    """
    Registry for user management domain event handlers.
    Manages registration and routing of events to appropriate handlers.
    """
    
    def __init__(self):
        self.handlers = [
            UserRegistrationHandler(),
            UserActivationHandler(),
            UserStatusHandler(),
            SubscriptionHandler(),
            ProfileHandler(),
            UserActivityHandler(),
        ]
    
    def get_handlers_for_event(self, event: BaseEvent) -> list[EventHandler]:
        """
        Get all handlers that can process the given event.
        
        Args:
            event: Event to find handlers for
            
        Returns:
            list[EventHandler]: List of handlers that can process the event
        """
        return [handler for handler in self.handlers if handler.can_handle(event)]
    
    async def handle_event(self, event: BaseEvent) -> None:
        """
        Handle event by routing to appropriate handlers.
        
        Args:
            event: Event to handle
        """
        handlers = self.get_handlers_for_event(event)
        
        if not handlers:
            logger.warning("No handlers found for event", 
                          event_type=event.event_type)
            return
        
        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error("Handler failed to process event", 
                           handler=handler.__class__.__name__,
                           event_type=event.event_type,
                           error=str(e))
                # Continue with other handlers even if one fails
                continue
    
    def register_handler(self, handler: EventHandler) -> None:
        """
        Register a new event handler.
        
        Args:
            handler: Event handler to register
        """
        if handler not in self.handlers:
            self.handlers.append(handler)
            logger.info("Event handler registered", 
                       handler=handler.__class__.__name__)
    
    def unregister_handler(self, handler: EventHandler) -> None:
        """
        Unregister an event handler.
        
        Args:
            handler: Event handler to unregister
        """
        if handler in self.handlers:
            self.handlers.remove(handler)
            logger.info("Event handler unregistered", 
                       handler=handler.__class__.__name__)


# Global registry instance
event_handler_registry = UserManagementEventHandlerRegistry()