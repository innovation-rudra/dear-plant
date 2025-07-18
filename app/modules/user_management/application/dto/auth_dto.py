# app/modules/user_management/application/dto/auth_dto.py
"""
Plant Care Application - Authentication DTOs

Data Transfer Objects for authentication-related operations in the Plant Care Application.
Defines data structures for login, registration, OAuth, and session management.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from app.modules.user_management.domain.models.user import User
from app.modules.user_management.domain.models.profile import Profile
from app.modules.user_management.domain.models.subscription import Subscription


@dataclass
class LoginDTO:
    """
    Login request data transfer object.
    Contains credentials for user authentication.
    """
    # Authentication credentials
    email: str
    password: str
    
    # Login context
    login_source: str = "web"  # web, mobile, api
    remember_me: bool = False
    
    # Security context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    
    # Two-factor authentication
    two_factor_code: Optional[str] = None
    backup_code: Optional[str] = None
    
    # Metadata
    timezone: Optional[str] = None
    language: str = "en"


@dataclass
class LoginResponseDTO:
    """
    Login response data transfer object.
    Contains authentication tokens and user information.
    """
    # Authentication tokens
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600  # seconds
    
    # User information
    user: Dict[str, Any] = field(default_factory=dict)
    profile: Dict[str, Any] = field(default_factory=dict)
    subscription: Dict[str, Any] = field(default_factory=dict)
    
    # Session information
    session_id: str = ""
    session_expires_at: str = ""
    
    # Feature access
    permissions: List[str] = field(default_factory=list)
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    
    # Plant Care specific
    plant_limit: int = 5
    subscription_tier: str = "free"
    is_expert_verified: bool = False
    
    # Onboarding status
    is_onboarded: bool = False
    onboarding_steps: List[str] = field(default_factory=list)
    
    # Security information
    last_login_at: Optional[str] = None
    password_expires_at: Optional[str] = None
    requires_password_change: bool = False
    
    # Metadata
    login_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    server_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class RegisterDTO:
    """
    Registration request data transfer object.
    Contains data for new user registration.
    """
    # Required registration fields
    email: str
    password: str
    display_name: str
    
    # Optional fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Plant Care preferences
    experience_level: str = "beginner"
    preferred_units: str = "metric"
    location: Optional[str] = None
    timezone: Optional[str] = None
    
    # Plant Care preferences
    plant_care_preferences: Dict[str, Any] = field(default_factory=dict)
    notification_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Subscription preferences
    subscription_tier: str = "free"
    start_trial: bool = False
    
    # Registration context
    registration_source: str = "web"  # web, mobile, referral, admin
    referral_code: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    
    # Legal consents
    terms_accepted: bool = False
    privacy_policy_accepted: bool = False
    marketing_consent: bool = False
    
    # Security context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    
    # Metadata
    language: str = "en"
    country: Optional[str] = None


@dataclass
class RegisterResponseDTO:
    """
    Registration response data transfer object.
    Contains registration result and user information.
    """
    # Registration result
    success: bool = True
    user_id: str = ""
    
    # User information
    user: Dict[str, Any] = field(default_factory=dict)
    profile: Dict[str, Any] = field(default_factory=dict)
    subscription: Dict[str, Any] = field(default_factory=dict)
    
    # Email verification
    email_verification_required: bool = True
    email_verification_sent: bool = False
    
    # Authentication tokens (if auto-login enabled)
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    session_id: Optional[str] = None
    
    # Onboarding information
    onboarding_required: bool = True
    onboarding_steps: List[str] = field(default_factory=list)
    
    # Welcome information
    welcome_message: str = ""
    next_steps: List[str] = field(default_factory=list)
    
    # Plant Care specific
    plant_limit: int = 5
    subscription_tier: str = "free"
    trial_available: bool = True
    
    # Metadata
    registration_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    server_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class OAuthLoginDTO:
    """
    OAuth login request data transfer object.
    Contains OAuth provider information and authorization code.
    """
    # OAuth provider information
    provider: str  # google, apple, facebook
    authorization_code: str
    redirect_uri: str
    
    # OAuth specific data
    state: Optional[str] = None
    code_verifier: Optional[str] = None  # For PKCE
    
    # Login context
    login_source: str = "web"
    
    # Security context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    
    # Registration preferences (for new users)
    subscription_tier: str = "free"
    start_trial: bool = False
    marketing_consent: bool = False
    
    # Metadata
    timezone: Optional[str] = None
    language: str = "en"


@dataclass
class OAuthResponseDTO:
    """
    OAuth response data transfer object.
    Contains OAuth authentication result and user information.
    """
    # Authentication result
    success: bool = True
    is_new_user: bool = False
    
    # Authentication tokens
    access_token: str = ""
    refresh_token: str = ""
    token_type: str = "Bearer"
    expires_in: int = 3600
    
    # User information
    user: Dict[str, Any] = field(default_factory=dict)
    profile: Dict[str, Any] = field(default_factory=dict)
    subscription: Dict[str, Any] = field(default_factory=dict)
    
    # OAuth provider information
    provider: str = ""
    provider_user_id: str = ""
    
    # Session information
    session_id: str = ""
    session_expires_at: str = ""
    
    # Email verification (usually not required for OAuth)
    email_verification_required: bool = False
    
    # Onboarding status
    onboarding_required: bool = False
    onboarding_steps: List[str] = field(default_factory=list)
    
    # Feature access
    permissions: List[str] = field(default_factory=list)
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    
    # Plant Care specific
    plant_limit: int = 5
    subscription_tier: str = "free"
    is_expert_verified: bool = False
    
    # Metadata
    login_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    server_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TokenRefreshDTO:
    """
    Token refresh request data transfer object.
    Contains refresh token for getting new access token.
    """
    # Token information
    refresh_token: str
    
    # Security context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    
    # Metadata
    requested_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TokenResponseDTO:
    """
    Token response data transfer object.
    Contains new authentication tokens.
    """
    # New tokens
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    
    # Token metadata
    issued_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: str = ""
    
    # User context (minimal for security)
    user_id: str = ""
    email: str = ""
    role: str = "user"
    
    # Feature access (might have changed)
    permissions: List[str] = field(default_factory=list)
    subscription_tier: str = "free"
    
    # Security information
    session_id: str = ""
    last_activity: str = ""


@dataclass
class PasswordResetDTO:
    """
    Password reset data transfer object.
    Contains password reset request and new password data.
    """
    # For password reset request
    email: Optional[str] = None
    
    # For password reset completion
    reset_token: Optional[str] = None
    new_password: Optional[str] = None
    confirm_password: Optional[str] = None
    
    # Security context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Metadata
    requested_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    request_source: str = "web"


@dataclass
class EmailVerificationDTO:
    """
    Email verification data transfer object.
    Contains email verification token and user information.
    """
    # Verification data
    verification_token: str
    email: str
    
    # User context
    user_id: Optional[str] = None
    
    # Security context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Metadata
    verified_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    verification_source: str = "web"


@dataclass
class SessionDTO:
    """
    Session data transfer object.
    Contains session information and user context.
    """
    # Session information
    session_id: str
    user_id: str
    
    # Session lifecycle
    created_at: str
    expires_at: str
    last_activity_at: str
    is_active: bool = True
    
    # Session context
    login_source: str = "web"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    
    # User context
    user_email: str = ""
    user_role: str = "user"
    subscription_tier: str = "free"
    
    # Security information
    is_suspicious: bool = False
    security_alerts: List[str] = field(default_factory=list)
    
    # Session metadata
    session_duration: int = 0  # seconds
    requests_count: int = 0
    last_request_at: Optional[str] = None


# Factory functions for creating DTOs from domain models

def create_login_response_dto(user: User, profile: Profile, subscription: Optional[Subscription],
                            access_token: str, refresh_token: str, session_id: str,
                            permissions: List[str]) -> LoginResponseDTO:
    """
    Create LoginResponseDTO from domain models and tokens.
    
    Args:
        user: User domain model
        profile: Profile domain model
        subscription: Subscription domain model (optional)
        access_token: JWT access token
        refresh_token: JWT refresh token
        session_id: Session identifier
        permissions: User permissions list
        
    Returns:
        LoginResponseDTO: Complete login response
    """
    # User information
    user_info = {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role.value,
        "status": user.status.value,
        "is_verified": user.is_verified,
        "is_onboarded": user.is_onboarded,
        "plant_limit": user.plant_limit,
        "created_at": user.created_at.isoformat(),
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
    }
    
    # Profile information
    profile_info = {
        "profile_id": profile.profile_id,
        "display_name": profile.display_name,
        "avatar_url": profile.avatar_url,
        "location": profile.location,
        "experience_level": profile.experience_level.value,
        "is_expert_verified": profile.is_expert_verified,
        "followers_count": profile.followers_count,
        "following_count": profile.following_count
    }
    
    # Subscription information
    subscription_info = {}
    if subscription:
        subscription_info = {
            "subscription_id": subscription.subscription_id,
            "tier": subscription.tier.value,
            "status": subscription.status.value,
            "is_trial": subscription.is_trial(),
            "trial_end_date": subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
            "is_active": subscription.is_active()
        }
    
    # Generate feature flags
    feature_flags = _generate_feature_flags(user, subscription)
    
    # Calculate session expiry
    session_expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
    
    # Determine onboarding steps
    onboarding_steps = []
    if not user.is_onboarded:
        onboarding_steps = _get_onboarding_steps(user, profile, subscription)
    
    return LoginResponseDTO(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=3600,
        user=user_info,
        profile=profile_info,
        subscription=subscription_info,
        session_id=session_id,
        session_expires_at=session_expires_at,
        permissions=permissions,
        feature_flags=feature_flags,
        plant_limit=user.plant_limit,
        subscription_tier=subscription.tier.value if subscription else "free",
        is_expert_verified=profile.is_expert_verified,
        is_onboarded=user.is_onboarded,
        onboarding_steps=onboarding_steps,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        requires_password_change=False
    )


def create_oauth_response_dto(user: User, profile: Profile, subscription: Optional[Subscription],
                            access_token: str, refresh_token: str, session_id: str,
                            provider: str, provider_user_id: str, is_new_user: bool,
                            permissions: List[str]) -> OAuthResponseDTO:
    """
    Create OAuthResponseDTO from domain models and OAuth data.
    
    Args:
        user: User domain model
        profile: Profile domain model
        subscription: Subscription domain model (optional)
        access_token: JWT access token
        refresh_token: JWT refresh token
        session_id: Session identifier
        provider: OAuth provider name
        provider_user_id: Provider-specific user ID
        is_new_user: Whether this is a new user registration
        permissions: User permissions list
        
    Returns:
        OAuthResponseDTO: Complete OAuth response
    """
    # User information
    user_info = {
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role.value,
        "status": user.status.value,
        "is_verified": user.is_verified,
        "provider": user.provider,
        "created_at": user.created_at.isoformat()
    }
    
    # Profile information
    profile_info = {
        "profile_id": profile.profile_id,
        "display_name": profile.display_name,
        "avatar_url": profile.avatar_url,
        "location": profile.location,
        "experience_level": profile.experience_level.value,
        "is_expert_verified": profile.is_expert_verified
    }
    
    # Subscription information
    subscription_info = {}
    if subscription:
        subscription_info = {
            "subscription_id": subscription.subscription_id,
            "tier": subscription.tier.value,
            "status": subscription.status.value,
            "is_trial": subscription.is_trial(),
            "is_active": subscription.is_active()
        }
    
    # Generate feature flags
    feature_flags = _generate_feature_flags(user, subscription)
    
    # Calculate session expiry
    session_expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
    
    # Determine onboarding steps for new users
    onboarding_steps = []
    onboarding_required = False
    if is_new_user or not user.is_onboarded:
        onboarding_required = True
        onboarding_steps = _get_onboarding_steps(user, profile, subscription)
    
    return OAuthResponseDTO(
        success=True,
        is_new_user=is_new_user,
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=3600,
        user=user_info,
        profile=profile_info,
        subscription=subscription_info,
        provider=provider,
        provider_user_id=provider_user_id,
        session_id=session_id,
        session_expires_at=session_expires_at,
        email_verification_required=False,  # OAuth users are pre-verified
        onboarding_required=onboarding_required,
        onboarding_steps=onboarding_steps,
        permissions=permissions,
        feature_flags=feature_flags,
        plant_limit=user.plant_limit,
        subscription_tier=subscription.tier.value if subscription else "free",
        is_expert_verified=profile.is_expert_verified
    )


def create_session_dto(session_data: Dict[str, Any], user: User) -> SessionDTO:
    """
    Create SessionDTO from session data and user.
    
    Args:
        session_data: Session data dictionary
        user: User domain model
        
    Returns:
        SessionDTO: Session data transfer object
    """
    # Calculate session duration
    created_at = datetime.fromisoformat(session_data["created_at"])
    session_duration = int((datetime.utcnow() - created_at).total_seconds())
    
    return SessionDTO(
        session_id=session_data["session_id"],
        user_id=user.user_id,
        created_at=session_data["created_at"],
        expires_at=session_data["expires_at"],
        last_activity_at=session_data.get("last_activity_at", session_data["created_at"]),
        is_active=session_data.get("is_active", True),
        login_source=session_data.get("login_source", "web"),
        ip_address=session_data.get("ip_address"),
        user_agent=session_data.get("user_agent"),
        device_info=session_data.get("device_info"),
        user_email=user.email,
        user_role=user.role.value,
        subscription_tier=user.subscription.tier.value if user.subscription else "free",
        is_suspicious=False,
        security_alerts=[],
        session_duration=session_duration,
        requests_count=session_data.get("requests_count", 0),
        last_request_at=session_data.get("last_request_at")
    )


def _generate_feature_flags(user: User, subscription: Optional[Subscription]) -> Dict[str, bool]:
    """Generate feature flags for user."""
    flags = {
        "premium_features": False,
        "unlimited_plants": False,
        "ai_identification": True,
        "expert_consultations": False,
        "advanced_analytics": False,
        "data_export": False,
        "family_sharing": False,
        "priority_support": False,
        "offline_mode": False,
        "expert_tools": False,
        "community_moderation": False
    }
    
    if subscription and subscription.is_active():
        if subscription.tier.value in ["premium", "expert", "family"]:
            flags.update({
                "premium_features": True,
                "unlimited_plants": True,
                "expert_consultations": True,
                "advanced_analytics": True,
                "data_export": True,
                "family_sharing": True,
                "priority_support": True,
                "offline_mode": True
            })
        
        if subscription.tier.value == "expert":
            flags.update({
                "expert_tools": True,
                "community_moderation": True
            })
    
    return flags


def _get_onboarding_steps(user: User, profile: Profile, subscription: Optional[Subscription]) -> List[str]:
    """Get onboarding steps for user."""
    steps = []
    
    if not user.is_verified:
        steps.append("verify_email")
    
    if not profile.avatar_url:
        steps.append("upload_avatar")
    
    if not profile.location:
        steps.append("set_location")
    
    if not profile.plant_care_preferences:
        steps.append("set_plant_preferences")
    
    if not profile.notification_preferences:
        steps.append("set_notifications")
    
    if profile.experience_level.value == "beginner":
        steps.append("set_experience_level")
    
    if subscription and subscription.tier.value == "free":
        steps.append("explore_premium_features")
    
    steps.append("add_first_plant")
    steps.append("complete_profile")
    
    return steps