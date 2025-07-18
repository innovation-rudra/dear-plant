"""
app/api/v1/admin.py
Plant Care Application - Admin Endpoints

Administrative endpoints for Plant Care Application management,
monitoring, and system operations. Requires admin privileges.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
import structlog

from app.shared.config.settings import get_settings
from app.shared.core.dependencies import get_admin_user, get_database_session, get_redis_session
from app.shared.utils.formatters import format_success_response, format_error_response
from app.shared.utils.validators import validate_pagination_params
from app.shared.infrastructure.cache.redis_client import get_redis_manager

# Setup logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

# Create admin router
admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_admin_user)],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin privileges required"},
        404: {"description": "Resource not found"},
        500: {"description": "Internal server error"},
    }
)

@admin_router.get("/", summary="Admin Dashboard Overview")
async def get_admin_dashboard(admin_user: dict = Depends(get_admin_user)):
    """
    Get admin dashboard overview with system statistics and key metrics.
    """
    try:
        # Placeholder data - will be replaced with actual queries
        dashboard_data = {
            "system_stats": {
                "total_users": 1250,
                "active_users_today": 89,
                "total_plants": 3420,
                "plants_added_today": 15,
                "care_tasks_completed_today": 156,
                "premium_users": 78,
                "conversion_rate": 6.2
            },
            "performance_metrics": {
                "avg_response_time_ms": 145,
                "api_requests_today": 4532,
                "error_rate_24h": 0.8,
                "cache_hit_rate": 94.5
            },
            "alerts": [
                {
                    "id": "alert_1",
                    "type": "performance",
                    "severity": "medium",
                    "message": "API response time increased by 15% in the last hour",
                    "timestamp": "2024-07-19T10:30:00Z"
                }
            ],
            "recent_activity": [
                {
                    "action": "user_registration",
                    "details": "New user registered: plant_lover_123",
                    "timestamp": "2024-07-19T11:45:00Z"
                },
                {
                    "action": "premium_upgrade",
                    "details": "User upgraded to premium: garden_expert",
                    "timestamp": "2024-07-19T11:30:00Z"
                }
            ]
        }
        
        logger.info("Admin dashboard accessed", admin_user_id=admin_user["user_id"])
        
        return format_success_response(
            data=dashboard_data,
            message="Admin dashboard retrieved successfully"
        )
        
    except Exception as e:
        logger.error("Error getting admin dashboard", error=str(e), admin_user_id=admin_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admin dashboard"
        )

@admin_router.get("/users", summary="Manage Users")
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search users by email or name"),
    role: Optional[str] = Query(None, description="Filter by user role"),
    status: Optional[str] = Query(None, description="Filter by user status"),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get users list with filtering, searching, and pagination.
    Admin can view and manage all users in the system.
    """
    try:
        # Validate pagination
        page, size = validate_pagination_params(page, size)
        
        # Placeholder data - will be replaced with actual database queries
        users_data = [
            {
                "user_id": "user_123",
                "email": "plant_lover@example.com",
                "display_name": "Plant Lover",
                "role": "user",
                "subscription_status": "premium_monthly",
                "is_active": True,
                "total_plants": 5,
                "last_login": "2024-07-19T09:30:00Z",
                "created_at": "2024-06-15T14:20:00Z",
                "total_revenue": 29.99
            },
            {
                "user_id": "user_456",
                "email": "garden_expert@example.com",
                "display_name": "Garden Expert",
                "role": "expert",
                "subscription_status": "free",
                "is_active": True,
                "total_plants": 12,
                "last_login": "2024-07-19T08:15:00Z",
                "created_at": "2024-05-20T10:45:00Z",
                "total_revenue": 0.00
            }
        ]
        
        total_count = len(users_data)
        total_pages = (total_count + size - 1) // size
        
        metadata = {
            "pagination": {
                "total_items": total_count,
                "current_page": page,
                "page_size": size,
                "total_pages": total_pages,
                "has_next_page": page < total_pages,
                "has_previous_page": page > 1
            },
            "filters": {
                "search": search,
                "role": role,
                "status": status
            }
        }
        
        logger.info("Users list accessed", admin_user_id=admin_user["user_id"], page=page, size=size)
        
        return format_success_response(
            data=users_data,
            message="Users retrieved successfully",
            metadata=metadata
        )
        
    except Exception as e:
        logger.error("Error getting users", error=str(e), admin_user_id=admin_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@admin_router.get("/users/{user_id}", summary="Get User Details")
async def get_user_details(
    user_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get detailed information about a specific user.
    """
    try:
        # Placeholder data - will be replaced with actual database query
        user_details = {
            "user_id": user_id,
            "email": "plant_lover@example.com",
            "display_name": "Plant Lover",
            "role": "user",
            "subscription_status": "premium_monthly",
            "is_active": True,
            "profile": {
                "avatar_url": "https://example.com/avatar.jpg",
                "timezone": "UTC",
                "language": "en",
                "units": "metric"
            },
            "stats": {
                "total_plants": 5,
                "care_streak_days": 12,
                "completion_rate": 85.5,
                "total_photos": 23,
                "community_posts": 3,
                "last_login": "2024-07-19T09:30:00Z"
            },
            "subscription": {
                "plan": "premium_monthly",
                "started_at": "2024-06-15T14:20:00Z",
                "next_billing_date": "2024-08-15T14:20:00Z",
                "total_revenue": 59.98,
                "payment_method": "card_ending_4242"
            },
            "activity": [
                {
                    "action": "plant_added",
                    "details": "Added new plant: Fiddle Leaf Fig",
                    "timestamp": "2024-07-19T08:30:00Z"
                },
                {
                    "action": "care_task_completed",
                    "details": "Watered Monstera Deliciosa",
                    "timestamp": "2024-07-18T19:15:00Z"
                }
            ]
        }
        
        logger.info("User details accessed", admin_user_id=admin_user["user_id"], target_user_id=user_id)
        
        return format_success_response(
            data=user_details,
            message="User details retrieved successfully"
        )
        
    except Exception as e:
        logger.error("Error getting user details", error=str(e), admin_user_id=admin_user["user_id"], target_user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user details"
        )

@admin_router.patch("/users/{user_id}/status", summary="Update User Status")
async def update_user_status(
    user_id: str,
    action: str,  # activate, deactivate, suspend
    reason: Optional[str] = None,
    admin_user: dict = Depends(get_admin_user)
):
    """
    Update user status (activate, deactivate, suspend).
    """
    try:
        valid_actions = ["activate", "deactivate", "suspend"]
        if action not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action. Must be one of: {valid_actions}"
            )
        
        # Placeholder - will be replaced with actual user status update
        updated_user = {
            "user_id": user_id,
            "status": action + "d",  # activated, deactivated, suspended
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": admin_user["user_id"],
            "reason": reason
        }
        
        logger.info(
            "User status updated",
            admin_user_id=admin_user["user_id"],
            target_user_id=user_id,
            action=action,
            reason=reason
        )
        
        return format_success_response(
            data=updated_user,
            message=f"User {action}d successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating user status", error=str(e), admin_user_id=admin_user["user_id"], target_user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user status"
        )

@admin_router.get("/analytics", summary="System Analytics")
async def get_system_analytics(
    period: str = Query("30d", description="Analytics period (7d, 30d, 90d, 1y)"),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get comprehensive system analytics and business metrics.
    """
    try:
        valid_periods = ["7d", "30d", "90d", "1y"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid period. Must be one of: {valid_periods}"
            )
        
        # Placeholder analytics data - will be replaced with actual queries
        analytics_data = {
            "period": period,
            "user_metrics": {
                "total_users": 1250,
                "new_users": 45,
                "active_users": 892,
                "retention_rate": 78.5,
                "churn_rate": 3.2
            },
            "plant_metrics": {
                "total_plants": 3420,
                "new_plants": 156,
                "avg_plants_per_user": 2.7,
                "most_popular_species": [
                    {"species": "Ficus lyrata", "count": 89},
                    {"species": "Monstera deliciosa", "count": 76},
                    {"species": "Pothos", "count": 65}
                ]
            },
            "engagement_metrics": {
                "care_tasks_completed": 2145,
                "completion_rate": 84.2,
                "photos_uploaded": 567,
                "community_posts": 123,
                "ai_chat_sessions": 445
            },
            "revenue_metrics": {
                "total_revenue": 2849.50,
                "new_subscriptions": 12,
                "subscription_revenue": 2640.00,
                "average_revenue_per_user": 2.28,
                "conversion_rate": 6.8
            },
            "technical_metrics": {
                "avg_response_time_ms": 145,
                "error_rate": 0.8,
                "uptime_percentage": 99.9,
                "cache_hit_rate": 94.5
            }
        }
        
        logger.info("System analytics accessed", admin_user_id=admin_user["user_id"], period=period)
        
        return format_success_response(
            data=analytics_data,
            message="System analytics retrieved successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting system analytics", error=str(e), admin_user_id=admin_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system analytics"
        )

@admin_router.get("/content/reports", summary="Content Reports")
async def get_content_reports(
    type: str = Query("flagged", description="Report type (flagged, spam, inappropriate)"),
    status: str = Query("pending", description="Report status (pending, resolved, dismissed)"),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get content moderation reports and flagged content.
    """
    try:
        # Placeholder data - will be replaced with actual content reports
        reports_data = [
            {
                "report_id": "report_123",
                "content_type": "community_post",
                "content_id": "post_456",
                "reported_by": "user_789",
                "reason": "inappropriate_content",
                "status": "pending",
                "content_preview": "This plant care advice seems questionable...",
                "created_at": "2024-07-19T10:15:00Z",
                "reporter_details": {
                    "user_id": "user_789",
                    "username": "concerned_gardener",
                    "reputation": 4.5
                }
            }
        ]
        
        logger.info("Content reports accessed", admin_user_id=admin_user["user_id"], type=type, status=status)
        
        return format_success_response(
            data=reports_data,
            message="Content reports retrieved successfully"
        )
        
    except Exception as e:
        logger.error("Error getting content reports", error=str(e), admin_user_id=admin_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve content reports"
        )

@admin_router.patch("/content/reports/{report_id}", summary="Handle Content Report")
async def handle_content_report(
    report_id: str,
    action: str,  # approve, remove, dismiss
    notes: Optional[str] = None,
    admin_user: dict = Depends(get_admin_user)
):
    """
    Handle content moderation report (approve, remove, dismiss).
    """
    try:
        valid_actions = ["approve", "remove", "dismiss"]
        if action not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action. Must be one of: {valid_actions}"
            )
        
        # Placeholder - will be replaced with actual report handling
        handled_report = {
            "report_id": report_id,
            "action": action,
            "status": "resolved",
            "handled_by": admin_user["user_id"],
            "handled_at": datetime.utcnow().isoformat(),
            "notes": notes
        }
        
        logger.info(
            "Content report handled",
            admin_user_id=admin_user["user_id"],
            report_id=report_id,
            action=action,
            notes=notes
        )
        
        return format_success_response(
            data=handled_report,
            message=f"Content report {action}d successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error handling content report", error=str(e), admin_user_id=admin_user["user_id"], report_id=report_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to handle content report"
        )

@admin_router.get("/system/logs", summary="System Logs")
async def get_system_logs(
    level: str = Query("INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to retrieve"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Get system logs for debugging and monitoring.
    """
    try:
        # Placeholder logs - will be replaced with actual log retrieval
        logs_data = [
            {
                "timestamp": "2024-07-19T11:30:00Z",
                "level": "INFO",
                "service": "plant-care-api",
                "message": "User authentication successful",
                "user_id": "user_123",
                "request_id": "req_456"
            },
            {
                "timestamp": "2024-07-19T11:25:00Z",
                "level": "ERROR",
                "service": "plant-care-api",
                "message": "Failed to connect to plant identification API",
                "error": "Connection timeout",
                "request_id": "req_789"
            }
        ]
        
        logger.info("System logs accessed", admin_user_id=admin_user["user_id"], level=level, limit=limit)
        
        return format_success_response(
            data=logs_data,
            message="System logs retrieved successfully"
        )
        
    except Exception as e:
        logger.error("Error getting system logs", error=str(e), admin_user_id=admin_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system logs"
        )

@admin_router.post("/system/cache/clear", summary="Clear Cache")
async def clear_cache(
    cache_type: str = Query("all", description="Cache type to clear (all, user, plant, api)"),
    admin_user: dict = Depends(get_admin_user),
    redis_client = Depends(get_redis_session)
):
    """
    Clear system cache for troubleshooting and maintenance.
    """
    try:
        cleared_keys = 0
        
        if cache_type == "all":
            # Clear all cache keys
            keys = await redis_client.keys("*")
            if keys:
                cleared_keys = await redis_client.delete(*keys)
        elif cache_type == "user":
            # Clear user-related cache
            keys = await redis_client.keys("user:*")
            if keys:
                cleared_keys = await redis_client.delete(*keys)
        elif cache_type == "plant":
            # Clear plant-related cache
            keys = await redis_client.keys("plant:*")
            if keys:
                cleared_keys = await redis_client.delete(*keys)
        elif cache_type == "api":
            # Clear API response cache
            keys = await redis_client.keys("api:*")
            if keys:
                cleared_keys = await redis_client.delete(*keys)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cache type. Must be one of: all, user, plant, api"
            )
        
        cache_clear_result = {
            "cache_type": cache_type,
            "keys_cleared": cleared_keys,
            "cleared_at": datetime.utcnow().isoformat(),
            "cleared_by": admin_user["user_id"]
        }
        
        logger.info(
            "Cache cleared",
            admin_user_id=admin_user["user_id"],
            cache_type=cache_type,
            keys_cleared=cleared_keys
        )
        
        return format_success_response(
            data=cache_clear_result,
            message=f"Cache cleared successfully ({cleared_keys} keys)"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error clearing cache", error=str(e), admin_user_id=admin_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )

@admin_router.get("/system/stats", summary="System Statistics")
async def get_system_stats(admin_user: dict = Depends(get_admin_user)):
    """
    Get real-time system statistics and performance metrics.
    """
    try:
        # Placeholder stats - will be replaced with actual system metrics
        system_stats = {
            "api": {
                "uptime_hours": 168.5,
                "requests_per_minute": 45.2,
                "avg_response_time_ms": 145,
                "error_rate_percent": 0.8,
                "active_connections": 23
            },
            "database": {
                "total_connections": 8,
                "active_queries": 2,
                "slow_queries": 0,
                "db_size_gb": 2.4,
                "cache_hit_ratio": 96.8
            },
            "redis": {
                "memory_used_mb": 45.2,
                "memory_peak_mb": 52.1,
                "connected_clients": 15,
                "ops_per_sec": 234,
                "hit_rate_percent": 94.5
            },
            "storage": {
                "total_files": 1245,
                "total_size_gb": 8.7,
                "photos_count": 1180,
                "avg_file_size_kb": 156.3
            },
            "background_jobs": {
                "queued_tasks": 5,
                "processing_tasks": 2,
                "completed_tasks_24h": 1456,
                "failed_tasks_24h": 8
            }
        }
        
        logger.info("System stats accessed", admin_user_id=admin_user["user_id"])
        
        return format_success_response(
            data=system_stats,
            message="System statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error("Error getting system stats", error=str(e), admin_user_id=admin_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics"
        )

@admin_router.post("/system/maintenance", summary="System Maintenance")
async def system_maintenance(
    action: str,  # start, stop, restart
    component: str = Query("api", description="Component to maintain (api, workers, cache)"),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Perform system maintenance operations.
    """
    try:
        valid_actions = ["start", "stop", "restart"]
        valid_components = ["api", "workers", "cache"]
        
        if action not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action. Must be one of: {valid_actions}"
            )
        
        if component not in valid_components:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid component. Must be one of: {valid_components}"
            )
        
        # Placeholder maintenance operation
        maintenance_result = {
            "action": action,
            "component": component,
            "status": "completed",
            "performed_by": admin_user["user_id"],
            "performed_at": datetime.utcnow().isoformat(),
            "message": f"Successfully {action}ed {component}"
        }
        
        logger.info(
            "System maintenance performed",
            admin_user_id=admin_user["user_id"],
            action=action,
            component=component
        )
        
        return format_success_response(
            data=maintenance_result,
            message=f"System maintenance completed: {action} {component}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error performing system maintenance", error=str(e), admin_user_id=admin_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform system maintenance"
        )

@admin_router.get("/exports/users", summary="Export Users")
async def export_users(
    format: str = Query("csv", description="Export format (csv, json)"),
    admin_user: dict = Depends(get_admin_user)
):
    """
    Export users data for analysis or backup.
    """
    try:
        if format not in ["csv", "json"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Must be csv or json"
            )
        
        # Placeholder export data
        export_info = {
            "export_id": f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "format": format,
            "total_records": 1250,
            "file_size_kb": 89.5,
            "download_url": f"https://api.plantcare.app/admin/downloads/users_export_{format}",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "created_by": admin_user["user_id"],
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info("User export initiated", admin_user_id=admin_user["user_id"], format=format)
        
        return format_success_response(
            data=export_info,
            message="User export initiated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error exporting users", error=str(e), admin_user_id=admin_user["user_id"])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export users"
        )