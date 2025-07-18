# app/modules/user_management/domain/services/subscription_service.py
"""
Plant Care Application - Subscription Domain Service

Subscription management business logic for the Plant Care Application.
Handles premium subscriptions, feature limits, usage tracking, and billing.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal

import structlog

from app.modules.user_management.domain.models.user import User, UserRole
from app.modules.user_management.domain.models.subscription import (
    Subscription, SubscriptionTier, SubscriptionStatus, BillingCycle
)
from app.modules.user_management.domain.repositories.user_repository import UserRepository
from app.modules.user_management.domain.events.user_events import (
    SubscriptionCreated, SubscriptionUpgraded, SubscriptionDowngraded,
    SubscriptionCancelled, SubscriptionRenewed, SubscriptionExpired,
    TrialStarted, TrialExpired, PaymentProcessed, PaymentFailed,
    UsageLimitReached, FeatureAccessGranted
)
from app.shared.events.base import EventPublisher
from app.shared.core.exceptions import (
    ValidationError, ResourceNotFoundError, BusinessLogicError,
    PaymentError, UsageLimitExceededError
)
from app.shared.utils.helpers import PlantCareHelpers

# Setup logger
logger = structlog.get_logger(__name__)


class SubscriptionService:
    """
    Domain service for subscription management in Plant Care Application.
    Handles premium subscriptions, feature limits, and billing operations.
    """
    
    def __init__(self, 
                 user_repository: UserRepository,
                 event_publisher: EventPublisher):
        """
        Initialize subscription service.
        
        Args:
            user_repository: User data repository
            event_publisher: Event publisher for domain events
        """
        self.user_repository = user_repository
        self.event_publisher = event_publisher
        
        # Subscription configuration
        self.trial_days = 14  # 14-day free trial
        self.grace_period_days = 3  # 3 days grace period after expiry
        
        # Feature limits by tier
        self.feature_limits = {
            SubscriptionTier.FREE: {
                "max_plants": 5,
                "ai_identifications_per_month": 10,
                "expert_consultations_per_month": 0,
                "advanced_analytics": False,
                "family_sharing": False,
                "export_data": False,
                "priority_support": False,
                "offline_mode": False
            },
            SubscriptionTier.PREMIUM: {
                "max_plants": -1,  # Unlimited
                "ai_identifications_per_month": 100,
                "expert_consultations_per_month": 5,
                "advanced_analytics": True,
                "family_sharing": True,
                "export_data": True,
                "priority_support": True,
                "offline_mode": True
            },
            SubscriptionTier.EXPERT: {
                "max_plants": -1,  # Unlimited
                "ai_identifications_per_month": 500,
                "expert_consultations_per_month": -1,  # Unlimited
                "advanced_analytics": True,
                "family_sharing": True,
                "export_data": True,
                "priority_support": True,
                "offline_mode": True,
                "expert_tools": True,
                "community_moderation": True
            },
            SubscriptionTier.FAMILY: {
                "max_plants": -1,  # Unlimited
                "ai_identifications_per_month": 300,
                "expert_consultations_per_month": 10,
                "advanced_analytics": True,
                "family_sharing": True,
                "export_data": True,
                "priority_support": True,
                "offline_mode": True,
                "max_family_members": 6
            }
        }
    
    async def create_subscription(self, 
                                user_id: str,
                                tier: SubscriptionTier,
                                billing_cycle: BillingCycle,
                                payment_method_id: Optional[str] = None,
                                coupon_code: Optional[str] = None,
                                start_trial: bool = True) -> Subscription:
        """
        Create a new subscription for Plant Care Application user.
        
        Args:
            user_id: User ID
            tier: Subscription tier
            billing_cycle: Monthly or yearly billing
            payment_method_id: Payment method identifier
            coupon_code: Optional discount coupon
            start_trial: Whether to start with trial period
            
        Returns:
            Subscription: Created subscription
            
        Raises:
            ValidationError: If subscription data is invalid
            ResourceNotFoundError: If user not found
            BusinessLogicError: If subscription cannot be created
        """
        try:
            logger.info("Creating subscription", user_id=user_id, tier=tier.value)
            
            # Validate user exists
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError(f"User not found: {user_id}")
            
            # Check if user already has active subscription
            if user.subscription and user.subscription.is_active():
                raise BusinessLogicError("User already has an active subscription")
            
            # Validate subscription data
            await self._validate_subscription_creation(user, tier, billing_cycle)
            
            # Calculate pricing
            pricing = await self._calculate_subscription_pricing(tier, billing_cycle, coupon_code)
            
            # Create subscription
            now = datetime.utcnow()
            
            # Determine trial and billing dates
            if start_trial and tier != SubscriptionTier.FREE:
                trial_end = now + timedelta(days=self.trial_days)
                next_billing_date = trial_end
                status = SubscriptionStatus.TRIAL
            else:
                trial_end = None
                next_billing_date = now + self._get_billing_interval(billing_cycle)
                status = SubscriptionStatus.ACTIVE if tier != SubscriptionTier.FREE else SubscriptionStatus.FREE
            
            subscription = Subscription(
                subscription_id=str(uuid.uuid4()),
                user_id=user_id,
                tier=tier,
                status=status,
                billing_cycle=billing_cycle,
                price=pricing["price"],
                currency=pricing["currency"],
                trial_end_date=trial_end,
                current_period_start=now,
                current_period_end=next_billing_date,
                next_billing_date=next_billing_date,
                payment_method_id=payment_method_id,
                created_at=now,
                updated_at=now
            )
            
            # Update user subscription
            user.subscription = subscription
            user.plant_limit = self._get_plant_limit(tier)
            user.updated_at = now
            
            # Save user with subscription
            await self.user_repository.update(user)
            
            # Publish events
            if start_trial and tier != SubscriptionTier.FREE:
                await self.event_publisher.publish(
                    TrialStarted(
                        user_id=user_id,
                        subscription_id=subscription.subscription_id,
                        tier=tier.value,
                        trial_end_date=trial_end,
                        started_at=now
                    )
                )
            
            await self.event_publisher.publish(
                SubscriptionCreated(
                    user_id=user_id,
                    subscription_id=subscription.subscription_id,
                    tier=tier.value,
                    billing_cycle=billing_cycle.value,
                    price=float(pricing["price"]),
                    currency=pricing["currency"],
                    created_at=now
                )
            )
            
            logger.info("Subscription created successfully", 
                       user_id=user_id, 
                       subscription_id=subscription.subscription_id)
            
            return subscription
            
        except (ValidationError, ResourceNotFoundError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error("Subscription creation failed", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to create subscription: {str(e)}")
    
    async def upgrade_subscription(self, 
                                 user_id: str,
                                 new_tier: SubscriptionTier,
                                 billing_cycle: Optional[BillingCycle] = None,
                                 prorate: bool = True) -> Subscription:
        """
        Upgrade user subscription to higher tier.
        
        Args:
            user_id: User ID
            new_tier: New subscription tier
            billing_cycle: New billing cycle (optional)
            prorate: Whether to prorate the billing
            
        Returns:
            Subscription: Updated subscription
            
        Raises:
            ValidationError: If upgrade data is invalid
            ResourceNotFoundError: If user/subscription not found
            BusinessLogicError: If upgrade is not valid
        """
        try:
            logger.info("Upgrading subscription", user_id=user_id, new_tier=new_tier.value)
            
            # Get user and current subscription
            user = await self.user_repository.find_by_id(user_id)
            if not user or not user.subscription:
                raise ResourceNotFoundError("User or subscription not found")
            
            current_subscription = user.subscription
            old_tier = current_subscription.tier
            
            # Validate upgrade
            await self._validate_subscription_upgrade(current_subscription, new_tier)
            
            # Calculate new pricing
            new_billing_cycle = billing_cycle or current_subscription.billing_cycle
            pricing = await self._calculate_subscription_pricing(new_tier, new_billing_cycle)
            
            # Calculate prorated amount if needed
            prorated_amount = Decimal('0')
            if prorate and current_subscription.status == SubscriptionStatus.ACTIVE:
                prorated_amount = await self._calculate_proration(current_subscription, pricing["price"])
            
            # Update subscription
            now = datetime.utcnow()
            current_subscription.tier = new_tier
            current_subscription.billing_cycle = new_billing_cycle
            current_subscription.price = pricing["price"]
            current_subscription.updated_at = now
            
            # Update user limits
            user.plant_limit = self._get_plant_limit(new_tier)
            user.updated_at = now
            
            # Save updated user
            await self.user_repository.update(user)
            
            # Publish upgrade event
            await self.event_publisher.publish(
                SubscriptionUpgraded(
                    user_id=user_id,
                    subscription_id=current_subscription.subscription_id,
                    old_tier=old_tier.value,
                    new_tier=new_tier.value,
                    prorated_amount=float(prorated_amount),
                    upgraded_at=now
                )
            )
            
            # Grant feature access
            await self.event_publisher.publish(
                FeatureAccessGranted(
                    user_id=user_id,
                    tier=new_tier.value,
                    features=list(self.feature_limits[new_tier].keys()),
                    granted_at=now
                )
            )
            
            logger.info("Subscription upgraded successfully", 
                       user_id=user_id, 
                       old_tier=old_tier.value,
                       new_tier=new_tier.value)
            
            return current_subscription
            
        except (ValidationError, ResourceNotFoundError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error("Subscription upgrade failed", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to upgrade subscription: {str(e)}")
    
    async def cancel_subscription(self, 
                                user_id: str,
                                cancel_immediately: bool = False,
                                cancellation_reason: Optional[str] = None) -> Subscription:
        """
        Cancel user subscription.
        
        Args:
            user_id: User ID
            cancel_immediately: Whether to cancel immediately or at period end
            cancellation_reason: Optional reason for cancellation
            
        Returns:
            Subscription: Updated subscription
            
        Raises:
            ResourceNotFoundError: If user/subscription not found
            BusinessLogicError: If cancellation is not valid
        """
        try:
            logger.info("Cancelling subscription", user_id=user_id, immediate=cancel_immediately)
            
            # Get user and subscription
            user = await self.user_repository.find_by_id(user_id)
            if not user or not user.subscription:
                raise ResourceNotFoundError("User or subscription not found")
            
            subscription = user.subscription
            
            # Validate cancellation
            if subscription.status in [SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED]:
                raise BusinessLogicError("Subscription is already cancelled or expired")
            
            now = datetime.utcnow()
            
            if cancel_immediately:
                # Cancel immediately
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.cancelled_at = now
                subscription.current_period_end = now
                
                # Downgrade to free tier
                subscription.tier = SubscriptionTier.FREE
                user.plant_limit = self._get_plant_limit(SubscriptionTier.FREE)
            else:
                # Cancel at period end
                subscription.cancel_at_period_end = True
                subscription.cancelled_at = now
            
            subscription.cancellation_reason = cancellation_reason
            subscription.updated_at = now
            user.updated_at = now
            
            # Save updated user
            await self.user_repository.update(user)
            
            # Publish cancellation event
            await self.event_publisher.publish(
                SubscriptionCancelled(
                    user_id=user_id,
                    subscription_id=subscription.subscription_id,
                    tier=subscription.tier.value,
                    cancelled_immediately=cancel_immediately,
                    cancellation_reason=cancellation_reason,
                    cancelled_at=now
                )
            )
            
            logger.info("Subscription cancelled successfully", 
                       user_id=user_id, 
                       immediate=cancel_immediately)
            
            return subscription
            
        except (ResourceNotFoundError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error("Subscription cancellation failed", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to cancel subscription: {str(e)}")
    
    async def check_feature_access(self, user_id: str, feature: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if user has access to specific Plant Care feature.
        
        Args:
            user_id: User ID
            feature: Feature name to check
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (has_access, feature_info)
            
        Raises:
            ResourceNotFoundError: If user not found
        """
        try:
            # Get user and subscription
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError(f"User not found: {user_id}")
            
            # Get current tier
            if user.subscription and user.subscription.is_active():
                tier = user.subscription.tier
            else:
                tier = SubscriptionTier.FREE
            
            # Get feature limits for tier
            tier_limits = self.feature_limits.get(tier, self.feature_limits[SubscriptionTier.FREE])
            
            # Check feature access
            has_access = tier_limits.get(feature, False)
            
            feature_info = {
                "feature": feature,
                "has_access": has_access,
                "current_tier": tier.value,
                "feature_limit": tier_limits.get(feature),
                "upgrade_required": not has_access and tier != SubscriptionTier.EXPERT
            }
            
            # Add usage information for countable features
            if feature in ["ai_identifications_per_month", "expert_consultations_per_month"]:
                usage_info = await self._get_feature_usage(user_id, feature)
                feature_info.update(usage_info)
            
            return has_access, feature_info
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            logger.error("Feature access check failed", user_id=user_id, feature=feature, error=str(e))
            return False, {"error": "Failed to check feature access"}
    
    async def track_feature_usage(self, user_id: str, feature: str, usage_count: int = 1) -> Dict[str, Any]:
        """
        Track usage of countable features.
        
        Args:
            user_id: User ID
            feature: Feature name
            usage_count: Number of uses to add
            
        Returns:
            Dict[str, Any]: Usage tracking result
            
        Raises:
            ResourceNotFoundError: If user not found
            UsageLimitExceededError: If usage limit exceeded
        """
        try:
            logger.debug("Tracking feature usage", user_id=user_id, feature=feature, count=usage_count)
            
            # Check feature access
            has_access, feature_info = await self.check_feature_access(user_id, feature)
            
            if not has_access:
                raise UsageLimitExceededError(f"No access to feature: {feature}")
            
            # Get current usage
            current_usage = await self._get_current_usage(user_id, feature)
            feature_limit = feature_info.get("feature_limit", 0)
            
            # Check if unlimited (-1) or within limits
            if feature_limit != -1 and (current_usage + usage_count) > feature_limit:
                # Publish usage limit reached event
                await self.event_publisher.publish(
                    UsageLimitReached(
                        user_id=user_id,
                        feature=feature,
                        current_usage=current_usage,
                        limit=feature_limit,
                        attempted_usage=usage_count,
                        reached_at=datetime.utcnow()
                    )
                )
                
                raise UsageLimitExceededError(
                    f"Feature usage limit exceeded. Current: {current_usage}, "
                    f"Limit: {feature_limit}, Attempted: {usage_count}"
                )
            
            # Track usage
            new_usage = await self._increment_usage(user_id, feature, usage_count)
            
            return {
                "feature": feature,
                "usage_tracked": usage_count,
                "total_usage": new_usage,
                "limit": feature_limit,
                "remaining": feature_limit - new_usage if feature_limit != -1 else -1
            }
            
        except (ResourceNotFoundError, UsageLimitExceededError):
            raise
        except Exception as e:
            logger.error("Feature usage tracking failed", user_id=user_id, feature=feature, error=str(e))
            raise BusinessLogicError(f"Failed to track feature usage: {str(e)}")
    
    async def process_subscription_renewal(self, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Process subscription renewal and payment.
        
        Args:
            user_id: User ID
            
        Returns:
            Tuple[bool, Dict[str, Any]]: (success, renewal_info)
            
        Raises:
            ResourceNotFoundError: If user/subscription not found
            PaymentError: If payment processing fails
        """
        try:
            logger.info("Processing subscription renewal", user_id=user_id)
            
            # Get user and subscription
            user = await self.user_repository.find_by_id(user_id)
            if not user or not user.subscription:
                raise ResourceNotFoundError("User or subscription not found")
            
            subscription = user.subscription
            
            # Validate renewal
            if subscription.status not in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]:
                raise BusinessLogicError("Subscription is not eligible for renewal")
            
            # Calculate renewal amount
            renewal_amount = subscription.price
            
            # Process payment (would integrate with payment processor)
            payment_result = await self._process_payment(
                user_id, 
                subscription.payment_method_id,
                renewal_amount,
                subscription.currency
            )
            
            if payment_result["success"]:
                # Update subscription for next period
                now = datetime.utcnow()
                next_period_end = subscription.current_period_end + self._get_billing_interval(subscription.billing_cycle)
                
                subscription.current_period_start = subscription.current_period_end
                subscription.current_period_end = next_period_end
                subscription.next_billing_date = next_period_end
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.updated_at = now
                
                # Reset trial status if applicable
                if subscription.status == SubscriptionStatus.TRIAL:
                    subscription.trial_end_date = now
                
                # Save updated subscription
                user.updated_at = now
                await self.user_repository.update(user)
                
                # Publish renewal events
                await self.event_publisher.publish(
                    PaymentProcessed(
                        user_id=user_id,
                        subscription_id=subscription.subscription_id,
                        amount=float(renewal_amount),
                        currency=subscription.currency,
                        payment_method_id=subscription.payment_method_id,
                        processed_at=now
                    )
                )
                
                await self.event_publisher.publish(
                    SubscriptionRenewed(
                        user_id=user_id,
                        subscription_id=subscription.subscription_id,
                        tier=subscription.tier.value,
                        renewed_until=next_period_end,
                        amount_paid=float(renewal_amount),
                        renewed_at=now
                    )
                )
                
                renewal_info = {
                    "subscription_id": subscription.subscription_id,
                    "amount_paid": float(renewal_amount),
                    "currency": subscription.currency,
                    "period_start": subscription.current_period_start.isoformat(),
                    "period_end": subscription.current_period_end.isoformat(),
                    "next_billing_date": subscription.next_billing_date.isoformat()
                }
                
                logger.info("Subscription renewed successfully", user_id=user_id)
                
                return True, renewal_info
            
            else:
                # Payment failed
                await self.event_publisher.publish(
                    PaymentFailed(
                        user_id=user_id,
                        subscription_id=subscription.subscription_id,
                        amount=float(renewal_amount),
                        currency=subscription.currency,
                        error_message=payment_result.get("error", "Payment failed"),
                        failed_at=datetime.utcnow()
                    )
                )
                
                raise PaymentError(f"Payment failed: {payment_result.get('error', 'Unknown error')}")
                
        except (ResourceNotFoundError, BusinessLogicError, PaymentError):
            raise
        except Exception as e:
            logger.error("Subscription renewal failed", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to process renewal: {str(e)}")
    
    # Private helper methods
    
    async def _validate_subscription_creation(self, user: User, tier: SubscriptionTier, 
                                            billing_cycle: BillingCycle) -> None:
        """Validate subscription creation data."""
        if tier == SubscriptionTier.EXPERT and user.role != UserRole.EXPERT:
            raise ValidationError("Expert subscription requires expert verification")
    
    async def _calculate_subscription_pricing(self, tier: SubscriptionTier, 
                                            billing_cycle: BillingCycle,
                                            coupon_code: Optional[str] = None) -> Dict[str, Any]:
        """Calculate subscription pricing with discounts."""
        # Base pricing (example pricing in USD)
        base_prices = {
            SubscriptionTier.FREE: {"monthly": Decimal('0'), "yearly": Decimal('0')},
            SubscriptionTier.PREMIUM: {"monthly": Decimal('9.99'), "yearly": Decimal('99.99')},
            SubscriptionTier.EXPERT: {"monthly": Decimal('19.99'), "yearly": Decimal('199.99')},
            SubscriptionTier.FAMILY: {"monthly": Decimal('14.99'), "yearly": Decimal('149.99')}
        }
        
        cycle_key = "monthly" if billing_cycle == BillingCycle.MONTHLY else "yearly"
        base_price = base_prices[tier][cycle_key]
        
        # Apply coupon discount if provided
        discount = Decimal('0')
        if coupon_code:
            discount = await self._calculate_coupon_discount(coupon_code, base_price)
        
        final_price = base_price - discount
        
        return {
            "price": final_price,
            "currency": "USD",
            "base_price": base_price,
            "discount": discount,
            "coupon_code": coupon_code
        }
    
    def _get_plant_limit(self, tier: SubscriptionTier) -> int:
        """Get plant limit for subscription tier."""
        limits = self.feature_limits.get(tier, self.feature_limits[SubscriptionTier.FREE])
        return limits.get("max_plants", 5)
    
    def _get_billing_interval(self, billing_cycle: BillingCycle) -> timedelta:
        """Get billing interval timedelta."""
        if billing_cycle == BillingCycle.MONTHLY:
            return timedelta(days=30)
        else:  # YEARLY
            return timedelta(days=365)
    
    async def _calculate_proration(self, subscription: Subscription, new_price: Decimal) -> Decimal:
        """Calculate prorated amount for subscription changes."""
        # Simplified proration calculation
        now = datetime.utcnow()
        period_total_days = (subscription.current_period_end - subscription.current_period_start).days
        remaining_days = (subscription.current_period_end - now).days
        
        if period_total_days <= 0:
            return Decimal('0')
        
        daily_rate_old = subscription.price / period_total_days
        daily_rate_new = new_price / period_total_days
        
        proration = (daily_rate_new - daily_rate_old) * remaining_days
        return max(proration, Decimal('0'))
    
    async def _get_feature_usage(self, user_id: str, feature: str) -> Dict[str, Any]:
        """Get current feature usage for user."""
        # This would typically query a usage tracking table
        # For now, return mock data
        return {
            "current_usage": 0,
            "monthly_limit": self.feature_limits[SubscriptionTier.FREE].get(feature, 0),
            "reset_date": datetime.utcnow().replace(day=1) + timedelta(days=32)
        }
    
    async def _get_current_usage(self, user_id: str, feature: str) -> int:
        """Get current usage count for feature."""
        # This would query usage tracking
        return 0
    
    async def _increment_usage(self, user_id: str, feature: str, count: int) -> int:
        """Increment usage count for feature."""
        # This would update usage tracking
        return count
    
    async def _process_payment(self, user_id: str, payment_method_id: Optional[str], 
                             amount: Decimal, currency: str) -> Dict[str, Any]:
        """Process payment through payment processor."""
        # Mock payment processing - would integrate with Stripe/Razorpay
        return {
            "success": True,
            "transaction_id": str(uuid.uuid4()),
            "amount": float(amount),
            "currency": currency
        }
    
    async def _calculate_coupon_discount(self, coupon_code: str, base_price: Decimal) -> Decimal:
        """Calculate discount from coupon code."""
        # Mock coupon processing
        return Decimal('0')


# Convenience functions for dependency injection
def create_subscription_service(user_repository: UserRepository,
                              event_publisher: EventPublisher) -> SubscriptionService:
    """Create subscription service instance."""
    return SubscriptionService(user_repository, event_publisher)