# app/modules/user_management/application/queries/__init__.py
"""
Plant Care Application - User Management Queries

Query objects for read operations in the Plant Care Application.
Implements CQRS pattern for user management data retrieval and analytics.
"""

from .user_queries import (
    GetUserByIdQuery,
    GetUserByEmailQuery,
    GetUserDashboardQuery,
    GetUserStatsQuery,
    SearchUsersQuery,
    GetUserActivityQuery,
    GetUserPreferencesQuery,
    GetUserSecurityInfoQuery
)

from .profile_queries import (
    GetProfileByUserIdQuery,
    GetExpertProfilesQuery,
    GetProfileFollowersQuery,
    GetProfileFollowingQuery,
    SearchProfilesQuery,
    GetProfileAnalyticsQuery,
    GetProfileCompletionQuery,
    GetNearbyProfilesQuery
)

from .subscription_queries import (
    GetUserSubscriptionQuery,
    GetSubscriptionUsageQuery,
    GetSubscriptionAnalyticsQuery,
    GetExpiringTrialsQuery,
    GetSubscriptionHistoryQuery,
    GetUsageReportsQuery,
    GetBillingHistoryQuery
)

from .analytics_queries import (
    GetUserAnalyticsQuery,
    GetExpertAnalyticsQuery,
    GetSubscriptionMetricsQuery,
    GetUserEngagementQuery,
    GetFeatureUsageQuery,
    GetRetentionAnalyticsQuery,
    GetCohortAnalysisQuery
)

__all__ = [
    # User Queries
    "GetUserByIdQuery",
    "GetUserByEmailQuery",
    "GetUserDashboardQuery",
    "GetUserStatsQuery",
    "SearchUsersQuery",
    "GetUserActivityQuery",
    "GetUserPreferencesQuery",
    "GetUserSecurityInfoQuery",
    
    # Profile Queries
    "GetProfileByUserIdQuery",
    "GetExpertProfilesQuery",
    "GetProfileFollowersQuery",
    "GetProfileFollowingQuery",
    "SearchProfilesQuery",
    "GetProfileAnalyticsQuery",
    "GetProfileCompletionQuery",
    "GetNearbyProfilesQuery",
    
    # Subscription Queries
    "GetUserSubscriptionQuery",
    "GetSubscriptionUsageQuery",
    "GetSubscriptionAnalyticsQuery",
    "GetExpiringTrialsQuery",
    "GetSubscriptionHistoryQuery",
    "GetUsageReportsQuery",
    "GetBillingHistoryQuery",
    
    # Analytics Queries
    "GetUserAnalyticsQuery",
    "GetExpertAnalyticsQuery",
    "GetSubscriptionMetricsQuery",
    "GetUserEngagementQuery",
    "GetFeatureUsageQuery",
    "GetRetentionAnalyticsQuery",
    "GetCohortAnalysisQuery"
]