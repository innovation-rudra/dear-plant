# app/modules/user_management/application/dto/__init__.py
"""
Plant Care Application - User Management DTOs

Data Transfer Objects for user management application layer.
Defines data structures for API requests, responses, and internal data transfer.
"""

from app.modules.user_management.application.dto.user_dto import (
    # User DTOs
    UserDTO,
    UserRegistrationDTO,
    UserUpdateDTO,
    UserDashboardDTO,
    UserStatsDTO,
    UserSearchResultDTO,
    UserBriefDTO,
    UserListDTO,
    
    # User factory functions
    create_user_dto,
    create_user_brief_dto,
    create_user_dashboard_dto
)

from app.modules.user_management.application.dto.profile_dto import (
    # Profile DTOs
    ProfileDTO,
    ProfileCreationDTO,
    ProfileUpdateDTO,
    ProfilePreferencesDTO,
    ProfileAvatarDTO,
    ProfileAnalyticsDTO,
    ProfileSearchResultDTO,
    ExpertProfileDTO,
    ProfileBriefDTO,
    
    # Profile factory functions
    create_profile_dto,
    create_expert_profile_dto,
    create_profile_brief_dto
)

from app.modules.user_management.application.dto.subscription_dto import (
    # Subscription DTOs
    SubscriptionDTO,
    SubscriptionCreationDTO,
    SubscriptionUpdateDTO,
    SubscriptionUsageDTO,
    SubscriptionAnalyticsDTO,
    FeatureUsageDTO,
    BillingDTO,
    TrialDTO,
    
    # Subscription factory functions
    create_subscription_dto,
    create_subscription_usage_dto,
    create_billing_dto
)

from app.modules.user_management.application.dto.auth_dto import (
    # Authentication DTOs
    LoginDTO,
    LoginResponseDTO,
    RegisterDTO,
    RegisterResponseDTO,
    OAuthLoginDTO,
    OAuthResponseDTO,
    TokenRefreshDTO,
    TokenResponseDTO,
    PasswordResetDTO,
    EmailVerificationDTO,
    SessionDTO,
    
    # Auth factory functions
    create_login_response_dto,
    create_oauth_response_dto,
    create_session_dto
)

__all__ = [
    # User DTOs
    "UserDTO",
    "UserRegistrationDTO",
    "UserUpdateDTO",
    "UserDashboardDTO",
    "UserStatsDTO",
    "UserSearchResultDTO",
    "UserBriefDTO",
    "UserListDTO",
    
    # User factory functions
    "create_user_dto",
    "create_user_brief_dto",
    "create_user_dashboard_dto",
    
    # Profile DTOs
    "ProfileDTO",
    "ProfileCreationDTO",
    "ProfileUpdateDTO",
    "ProfilePreferencesDTO",
    "ProfileAvatarDTO",
    "ProfileAnalyticsDTO",
    "ProfileSearchResultDTO",
    "ExpertProfileDTO",
    "ProfileBriefDTO",
    
    # Profile factory functions
    "create_profile_dto",
    "create_expert_profile_dto",
    "create_profile_brief_dto",
    
    # Subscription DTOs
    "SubscriptionDTO",
    "SubscriptionCreationDTO",
    "SubscriptionUpdateDTO",
    "SubscriptionUsageDTO",
    "SubscriptionAnalyticsDTO",
    "FeatureUsageDTO",
    "BillingDTO",
    "TrialDTO",
    
    # Subscription factory functions
    "create_subscription_dto",
    "create_subscription_usage_dto",
    "create_billing_dto",
    
    # Authentication DTOs
    "LoginDTO",
    "LoginResponseDTO",
    "RegisterDTO",
    "RegisterResponseDTO",
    "OAuthLoginDTO",
    "OAuthResponseDTO",
    "TokenRefreshDTO",
    "TokenResponseDTO",
    "PasswordResetDTO",
    "EmailVerificationDTO",
    "SessionDTO",
    
    # Auth factory functions
    "create_login_response_dto",
    "create_oauth_response_dto",
    "create_session_dto"
]