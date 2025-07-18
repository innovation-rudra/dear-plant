# app/modules/user_management/infrastructure/database/models.py
"""
Plant Care Application - User Management Database Models

SQLAlchemy models for user management in the Plant Care Application.
Maps domain entities to PostgreSQL database tables with proper relationships and constraints.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from decimal import Decimal

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, Numeric, 
    JSON, ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.mutable import MutableDict

# Base class for all models
Base = declarative_base()

# Enums for database
user_role_enum = ENUM('user', 'premium', 'expert', 'admin', name='user_role_enum')
user_status_enum = ENUM('pending', 'active', 'suspended', 'deleted', name='user_status_enum')
subscription_tier_enum = ENUM('free', 'premium', 'expert', 'family', name='subscription_tier_enum')
subscription_status_enum = ENUM('trial', 'active', 'cancelled', 'expired', 'free', name='subscription_status_enum')
billing_cycle_enum = ENUM('monthly', 'yearly', name='billing_cycle_enum')
profile_status_enum = ENUM('active', 'inactive', 'suspended', name='profile_status_enum')
experience_level_enum = ENUM('beginner', 'intermediate', 'advanced', 'expert', name='experience_level_enum')
preferred_units_enum = ENUM('metric', 'imperial', name='preferred_units_enum')
profile_visibility_enum = ENUM('public', 'private', 'followers_only', name='profile_visibility_enum')


class UserModel(Base):
    """
    User database model for Plant Care Application.
    Stores core user authentication and account information.
    """
    __tablename__ = 'users'
    
    # Primary key
    user_id = Column(UUID(as_uuid=False), primary_key=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    supabase_user_id = Column(String(255), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=True)  # For email auth
    provider = Column(String(50), nullable=False, default='email')  # email, google, apple, facebook
    
    # User information
    role = Column(user_role_enum, nullable=False, default='user')
    status = Column(user_status_enum, nullable=False, default='pending')
    is_verified = Column(Boolean, nullable=False, default=False)
    is_onboarded = Column(Boolean, nullable=False, default=False)
    
    # Plant Care specific limits
    plant_limit = Column(Integer, nullable=False, default=5)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    email_verified_at = Column(DateTime, nullable=True)
    onboarded_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Account management
    deletion_reason = Column(Text, nullable=True)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # Relationships
    profile = relationship("ProfileModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    subscription = relationship("SubscriptionModel", back_populates="user", uselist=False, cascade="all, delete-orphan")
    usage_tracking = relationship("UsageTrackingModel", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_users_email_status', 'email', 'status'),
        Index('idx_users_supabase_id', 'supabase_user_id'),
        Index('idx_users_created_at', 'created_at'),
        Index('idx_users_last_login', 'last_login_at'),
        CheckConstraint('plant_limit >= -1', name='check_plant_limit_valid'),
        CheckConstraint('failed_login_attempts >= 0', name='check_failed_attempts_positive'),
    )
    
    def __repr__(self):
        return f"<UserModel(user_id='{self.user_id}', email='{self.email}', role='{self.role}')>"


class ProfileModel(Base):
    """
    Profile database model for Plant Care Application.
    Stores extended user profile information, preferences, and social features.
    """
    __tablename__ = 'profiles'
    
    # Primary key
    profile_id = Column(UUID(as_uuid=False), primary_key=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey('users.user_id'), nullable=False, unique=True)
    
    # Basic profile information
    display_name = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    location = Column(String(200), nullable=True)
    timezone = Column(String(50), nullable=False, default='UTC')
    
    # Plant Care preferences
    experience_level = Column(experience_level_enum, nullable=False, default='beginner')
    preferred_units = Column(preferred_units_enum, nullable=False, default='metric')
    
    # Profile settings
    profile_visibility = Column(profile_visibility_enum, nullable=False, default='public')
    status = Column(profile_status_enum, nullable=False, default='active')
    
    # Expert verification
    is_expert_verified = Column(Boolean, nullable=False, default=False)
    expert_verification_status = Column(String(20), nullable=True)  # pending, verified, rejected
    expert_credentials = Column(MutableDict.as_mutable(JSON), nullable=True)
    expert_specialties = Column(JSON, nullable=True)  # Array of specialties
    verification_requested_at = Column(DateTime, nullable=True)
    verification_approved_at = Column(DateTime, nullable=True)
    verification_approved_by = Column(UUID(as_uuid=False), nullable=True)
    verification_notes = Column(Text, nullable=True)
    expert_rating = Column(Numeric(3, 2), nullable=True)  # 0.00 to 5.00
    expert_reviews_count = Column(Integer, nullable=False, default=0)
    
    # Social features
    followers_count = Column(Integer, nullable=False, default=0)
    following_count = Column(Integer, nullable=False, default=0)
    
    # Plant Care preferences (JSON)
    plant_care_preferences = Column(MutableDict.as_mutable(JSON), nullable=False, default=dict)
    notification_preferences = Column(MutableDict.as_mutable(JSON), nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="profile")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_profiles_user_id', 'user_id'),
        Index('idx_profiles_display_name', 'display_name'),
        Index('idx_profiles_location', 'location'),
        Index('idx_profiles_experience', 'experience_level'),
        Index('idx_profiles_expert_status', 'is_expert_verified', 'expert_verification_status'),
        Index('idx_profiles_visibility', 'profile_visibility', 'status'),
        CheckConstraint('followers_count >= 0', name='check_followers_positive'),
        CheckConstraint('following_count >= 0', name='check_following_positive'),
        CheckConstraint('expert_rating IS NULL OR (expert_rating >= 0 AND expert_rating <= 5)', 
                       name='check_expert_rating_range'),
    )
    
    def __repr__(self):
        return f"<ProfileModel(profile_id='{self.profile_id}', display_name='{self.display_name}')>"


class SubscriptionModel(Base):
    """
    Subscription database model for Plant Care Application.
    Stores subscription tiers, billing information, and payment tracking.
    """
    __tablename__ = 'subscriptions'
    
    # Primary key
    subscription_id = Column(UUID(as_uuid=False), primary_key=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey('users.user_id'), nullable=False, unique=True)
    
    # Subscription details
    tier = Column(subscription_tier_enum, nullable=False, default='free')
    status = Column(subscription_status_enum, nullable=False, default='free')
    billing_cycle = Column(billing_cycle_enum, nullable=True)  # NULL for free tier
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default='USD')
    
    # Trial information
    trial_end_date = Column(DateTime, nullable=True)
    
    # Billing periods
    current_period_start = Column(DateTime, nullable=False, default=datetime.utcnow)
    current_period_end = Column(DateTime, nullable=False, default=datetime.utcnow)
    next_billing_date = Column(DateTime, nullable=True)
    
    # Payment information
    payment_method_id = Column(String(255), nullable=True)
    last_payment_date = Column(DateTime, nullable=True)
    last_payment_amount = Column(Numeric(10, 2), nullable=True)
    
    # Subscription management
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="subscription")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_subscriptions_user_id', 'user_id'),
        Index('idx_subscriptions_tier_status', 'tier', 'status'),
        Index('idx_subscriptions_billing_date', 'next_billing_date'),
        Index('idx_subscriptions_trial_end', 'trial_end_date'),
        Index('idx_subscriptions_active', 'status', 'current_period_end'),
        CheckConstraint('price >= 0', name='check_price_positive'),
        CheckConstraint('last_payment_amount IS NULL OR last_payment_amount >= 0', 
                       name='check_payment_amount_positive'),
    )
    
    def __repr__(self):
        return f"<SubscriptionModel(subscription_id='{self.subscription_id}', tier='{self.tier}', status='{self.status}')>"


class UsageTrackingModel(Base):
    """
    Usage tracking database model for Plant Care Application.
    Tracks feature usage for subscription limits and analytics.
    """
    __tablename__ = 'usage_tracking'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey('users.user_id'), nullable=False)
    
    # Usage tracking
    feature = Column(String(100), nullable=False)  # ai_identifications, expert_consultations, etc.
    usage_count = Column(Integer, nullable=False, default=0)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("UserModel", back_populates="usage_tracking")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_usage_user_feature', 'user_id', 'feature'),
        Index('idx_usage_period', 'period_start', 'period_end'),
        Index('idx_usage_feature_period', 'feature', 'period_start', 'period_end'),
        UniqueConstraint('user_id', 'feature', 'period_start', name='uq_user_feature_period'),
        CheckConstraint('usage_count >= 0', name='check_usage_count_positive'),
        CheckConstraint('period_end > period_start', name='check_period_valid'),
    )
    
    def __repr__(self):
        return f"<UsageTrackingModel(user_id='{self.user_id}', feature='{self.feature}', usage='{self.usage_count}')>"


class FollowModel(Base):
    """
    Social following relationships for Plant Care Application.
    Tracks user-to-user following for community features.
    """
    __tablename__ = 'follows'
    
    # Composite primary key
    follower_id = Column(UUID(as_uuid=False), ForeignKey('users.user_id'), primary_key=True)
    following_id = Column(UUID(as_uuid=False), ForeignKey('users.user_id'), primary_key=True)
    
    # Follow metadata
    followed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    follower = relationship("UserModel", foreign_keys=[follower_id])
    following = relationship("UserModel", foreign_keys=[following_id])
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_follows_follower', 'follower_id'),
        Index('idx_follows_following', 'following_id'),
        Index('idx_follows_date', 'followed_at'),
        CheckConstraint('follower_id != following_id', name='check_no_self_follow'),
    )
    
    def __repr__(self):
        return f"<FollowModel(follower='{self.follower_id}', following='{self.following_id}')>"


class SessionModel(Base):
    """
    User session tracking for Plant Care Application.
    Stores active sessions for security and analytics.
    """
    __tablename__ = 'user_sessions'
    
    # Primary key
    session_id = Column(String(255), primary_key=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey('users.user_id'), nullable=False)
    
    # Session information
    login_source = Column(String(50), nullable=False)  # web, mobile, api
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSON, nullable=True)
    
    # Session lifecycle
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Security
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("UserModel")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_sessions_user_id', 'user_id'),
        Index('idx_sessions_expires', 'expires_at'),
        Index('idx_sessions_active', 'is_active', 'expires_at'),
        Index('idx_sessions_last_activity', 'last_activity_at'),
        CheckConstraint('expires_at > created_at', name='check_session_expiry_valid'),
    )
    
    def __repr__(self):
        return f"<SessionModel(session_id='{self.session_id}', user_id='{self.user_id}')>"


# Database initialization and utility functions
def create_all_tables(engine):
    """Create all user management tables."""
    Base.metadata.create_all(engine)


def drop_all_tables(engine):
    """Drop all user management tables (use with caution!)."""
    Base.metadata.drop_all(engine)


def get_table_names():
    """Get list of all table names in user management module."""
    return [table.name for table in Base.metadata.tables.values()]