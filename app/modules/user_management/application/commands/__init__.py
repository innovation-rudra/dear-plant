# app/modules/user_management/application/commands/__init__.py
"""
Plant Care Application - User Management Commands

Command objects for write operations in the Plant Care Application.
Implements CQRS pattern for user management business operations.
"""

from .user_commands import (
    RegisterUserCommand,
    ActivateUserCommand,
    DeactivateUserCommand,
    DeleteUserCommand,
    ChangePasswordCommand,
    VerifyEmailCommand
)

from .profile_commands import (
    CreateProfileCommand,
    UpdateProfileCommand,
    UpdateAvatarCommand,
    UpdatePreferencesCommand,
    RequestExpertVerificationCommand,
    ApproveExpertVerificationCommand,
    FollowUserCommand,
    UnfollowUserCommand
)

from .subscription_commands import (
    CreateSubscriptionCommand,
    UpgradeSubscriptionCommand,
    DowngradeSubscriptionCommand,
    CancelSubscriptionCommand,
    RenewSubscriptionCommand,
    StartTrialCommand
)

from .auth_commands import (
    LoginCommand,
    LogoutCommand,
    RefreshTokenCommand,
    OAuthLoginCommand,
    ResetPasswordCommand
)

__all__ = [
    # User Management Commands
    "RegisterUserCommand",
    "ActivateUserCommand", 
    "DeactivateUserCommand",
    "DeleteUserCommand",
    "ChangePasswordCommand",
    "VerifyEmailCommand",
    
    # Profile Management Commands
    "CreateProfileCommand",
    "UpdateProfileCommand",
    "UpdateAvatarCommand", 
    "UpdatePreferencesCommand",
    "RequestExpertVerificationCommand",
    "ApproveExpertVerificationCommand",
    "FollowUserCommand",
    "UnfollowUserCommand",
    
    # Subscription Management Commands
    "CreateSubscriptionCommand",
    "UpgradeSubscriptionCommand",
    "DowngradeSubscriptionCommand", 
    "CancelSubscriptionCommand",
    "RenewSubscriptionCommand",
    "StartTrialCommand",
    
    # Authentication Commands
    "LoginCommand",
    "LogoutCommand",
    "RefreshTokenCommand",
    "OAuthLoginCommand", 
    "ResetPasswordCommand"
]