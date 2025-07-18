"""
app/shared/utils/formatters.py
Plant Care Application - Data Formatters

Data formatting utilities for Plant Care Application including date formatting,
plant data serialization, care schedule formatting, and API response formatting.
"""
import json
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import structlog

from app.shared.config.settings import get_settings

# Setup logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()


class PlantCareFormatter:
    """
    Comprehensive data formatter for Plant Care Application.
    """
    
    @staticmethod
    def format_datetime(dt: Union[datetime, date, str, None], include_time: bool = True) -> Optional[str]:
        """
        Format datetime for Plant Care API responses.
        
        Args:
            dt: Datetime to format
            include_time: Whether to include time information
            
        Returns:
            Optional[str]: Formatted datetime string or None
        """
        if dt is None:
            return None
        
        try:
            if isinstance(dt, str):
                # Parse string datetime
                if 'T' in dt:
                    parsed_dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                else:
                    parsed_dt = datetime.strptime(dt, '%Y-%m-%d')
            elif isinstance(dt, date) and not isinstance(dt, datetime):
                parsed_dt = datetime.combine(dt, datetime.min.time())
            else:
                parsed_dt = dt
            
            if include_time:
                return parsed_dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            else:
                return parsed_dt.strftime('%Y-%m-%d')
                
        except (ValueError, TypeError) as e:
            logger.error("Error formatting datetime", datetime=str(dt), error=str(e))
            return None
    
    @staticmethod
    def format_care_frequency(frequency: str) -> str:
        """
        Format care frequency for user display.
        
        Args:
            frequency: Internal frequency code
            
        Returns:
            str: Human-readable frequency
        """
        frequency_mapping = {
            "daily": "Every day",
            "every_2_days": "Every 2 days",
            "every_3_days": "Every 3 days",
            "weekly": "Once a week",
            "bi_weekly": "Every 2 weeks",
            "monthly": "Once a month",
            "seasonal": "Seasonally",
            "as_needed": "As needed"
        }
        
        return frequency_mapping.get(frequency, frequency.replace('_', ' ').title())
    
    @staticmethod
    def format_health_status(status: str, severity: Optional[str] = None) -> Dict[str, Any]:
        """
        Format plant health status with visual indicators.
        
        Args:
            status: Health status code
            severity: Optional severity level
            
        Returns:
            Dict: Formatted health status with colors and descriptions
        """
        status_mapping = {
            "excellent": {
                "display_name": "Excellent",
                "description": "Plant is thriving and healthy",
                "color": "#4CAF50",
                "icon": "🌿",
                "priority": 1
            },
            "good": {
                "display_name": "Good",
                "description": "Plant is healthy with minor concerns",
                "color": "#8BC34A",
                "icon": "🌱",
                "priority": 2
            },
            "fair": {
                "display_name": "Fair",
                "description": "Plant shows some concerning signs",
                "color": "#FFC107",
                "icon": "⚠️",
                "priority": 3
            },
            "poor": {
                "display_name": "Poor",
                "description": "Plant needs immediate attention",
                "color": "#FF9800",
                "icon": "🚨",
                "priority": 4
            },
            "critical": {
                "display_name": "Critical",
                "description": "Plant is in critical condition",
                "color": "#F44336",
                "icon": "🆘",
                "priority": 5
            },
            "recovering": {
                "display_name": "Recovering",
                "description": "Plant is recovering from issues",
                "color": "#2196F3",
                "icon": "💚",
                "priority": 2
            },
            "unknown": {
                "display_name": "Unknown",
                "description": "Health status needs assessment",
                "color": "#9E9E9E",
                "icon": "❓",
                "priority": 3
            }
        }
        
        base_status = status_mapping.get(status, status_mapping["unknown"])
        
        # Adjust color intensity based on severity
        if severity:
            severity_adjustments = {
                "low": {"color_intensity": 0.7},
                "medium": {"color_intensity": 1.0},
                "high": {"color_intensity": 1.3},
                "critical": {"color_intensity": 1.5}
            }
            
            adjustment = severity_adjustments.get(severity, {})
            if "color_intensity" in adjustment:
                base_status["severity"] = severity
                base_status["severity_display"] = severity.title()
        
        return base_status
    
    @staticmethod
    def format_plant_summary(plant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format plant data for summary views.
        
        Args:
            plant_data: Raw plant data from database
            
        Returns:
            Dict: Formatted plant summary
        """
        try:
            summary = {
                "plant_id": plant_data.get("plant_id"),
                "name": plant_data.get("name", "Unnamed Plant"),
                "species": plant_data.get("species"),
                "nickname": plant_data.get("nickname"),
                "category": plant_data.get("category", "").replace('_', ' ').title(),
                "health_status": PlantCareFormatter.format_health_status(
                    plant_data.get("health_status", "unknown"),
                    plant_data.get("health_severity")
                ),
                "care_score": plant_data.get("care_score", 0),
                "days_owned": PlantCareFormatter.calculate_days_owned(
                    plant_data.get("acquired_date")
                ),
                "next_care": PlantCareFormatter.format_next_care_date(
                    plant_data.get("next_watering"),
                    plant_data.get("next_fertilizing")
                ),
                "photos": {
                    "thumbnail": plant_data.get("thumbnail_url"),
                    "latest": plant_data.get("latest_photo_url"),
                    "count": plant_data.get("photo_count", 0)
                },
                "growth_stage": plant_data.get("growth_stage", "").replace('_', ' ').title(),
                "location": plant_data.get("location"),
                "is_favorite": plant_data.get("is_favorite", False),
                "created_at": PlantCareFormatter.format_datetime(plant_data.get("created_at")),
                "updated_at": PlantCareFormatter.format_datetime(plant_data.get("updated_at"))
            }
            
            # Add care urgency indicator
            summary["care_urgency"] = PlantCareFormatter.calculate_care_urgency(
                plant_data.get("next_watering"),
                plant_data.get("last_watered"),
                plant_data.get("watering_frequency")
            )
            
            return summary
            
        except Exception as e:
            logger.error("Error formatting plant summary", error=str(e), plant_data=plant_data)
            return {"error": "Failed to format plant data", "plant_id": plant_data.get("plant_id")}
    
    @staticmethod
    def format_care_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format care task for mobile app display.
        
        Args:
            task_data: Raw care task data
            
        Returns:
            Dict: Formatted care task
        """
        try:
            task = {
                "task_id": task_data.get("task_id"),
                "plant_id": task_data.get("plant_id"),
                "plant_name": task_data.get("plant_name", "Unknown Plant"),
                "care_type": task_data.get("care_type", "").replace('_', ' ').title(),
                "care_icon": PlantCareFormatter.get_care_type_icon(task_data.get("care_type")),
                "scheduled_date": PlantCareFormatter.format_datetime(
                    task_data.get("scheduled_date"), include_time=False
                ),
                "completed_date": PlantCareFormatter.format_datetime(
                    task_data.get("completed_date")
                ),
                "is_completed": task_data.get("is_completed", False),
                "is_overdue": PlantCareFormatter.is_task_overdue(
                    task_data.get("scheduled_date"),
                    task_data.get("is_completed", False)
                ),
                "priority": PlantCareFormatter.calculate_task_priority(
                    task_data.get("scheduled_date"),
                    task_data.get("care_type"),
                    task_data.get("plant_health_status")
                ),
                "notes": task_data.get("notes"),
                "frequency": PlantCareFormatter.format_care_frequency(
                    task_data.get("frequency", "")
                ),
                "reminder_sent": task_data.get("reminder_sent", False),
                "created_at": PlantCareFormatter.format_datetime(task_data.get("created_at"))
            }
            
            # Add time-based display information
            task["time_info"] = PlantCareFormatter.format_task_timing(
                task_data.get("scheduled_date"),
                task_data.get("completed_date"),
                task_data.get("is_completed", False)
            )
            
            return task
            
        except Exception as e:
            logger.error("Error formatting care task", error=str(e), task_data=task_data)
            return {"error": "Failed to format task data", "task_id": task_data.get("task_id")}
    
    @staticmethod
    def format_community_post(post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format community post for social feed.
        
        Args:
            post_data: Raw post data from database
            
        Returns:
            Dict: Formatted community post
        """
        try:
            post = {
                "post_id": post_data.get("post_id"),
                "title": post_data.get("title"),
                "content": PlantCareFormatter.format_post_content(
                    post_data.get("content", "")
                ),
                "author": {
                    "user_id": post_data.get("author_id"),
                    "username": post_data.get("author_username", "Anonymous"),
                    "display_name": post_data.get("author_display_name"),
                    "avatar_url": post_data.get("author_avatar_url"),
                    "is_expert": post_data.get("author_is_expert", False),
                    "expertise_areas": post_data.get("author_expertise_areas", [])
                },
                "plant_info": {
                    "plant_id": post_data.get("plant_id"),
                    "plant_name": post_data.get("plant_name"),
                    "species": post_data.get("plant_species")
                } if post_data.get("plant_id") else None,
                "engagement": {
                    "likes_count": post_data.get("likes_count", 0),
                    "comments_count": post_data.get("comments_count", 0),
                    "shares_count": post_data.get("shares_count", 0),
                    "is_liked": post_data.get("is_liked_by_user", False),
                    "is_saved": post_data.get("is_saved_by_user", False)
                },
                "media": {
                    "photos": post_data.get("photo_urls", []),
                    "videos": post_data.get("video_urls", []),
                    "thumbnail": post_data.get("thumbnail_url")
                },
                "tags": post_data.get("tags", []),
                "category": post_data.get("category", "general"),
                "visibility": post_data.get("visibility", "public"),
                "created_at": PlantCareFormatter.format_datetime(post_data.get("created_at")),
                "updated_at": PlantCareFormatter.format_datetime(post_data.get("updated_at"))
            }
            
            # Add time-ago display
            post["time_ago"] = PlantCareFormatter.format_time_ago(
                post_data.get("created_at")
            )
            
            return post
            
        except Exception as e:
            logger.error("Error formatting community post", error=str(e), post_data=post_data)
            return {"error": "Failed to format post data", "post_id": post_data.get("post_id")}
    
    @staticmethod
    def format_analytics_data(analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format analytics data for dashboard display.
        
        Args:
            analytics_data: Raw analytics data
            
        Returns:
            Dict: Formatted analytics data
        """
        try:
            analytics = {
                "overview": {
                    "total_plants": analytics_data.get("total_plants", 0),
                    "healthy_plants": analytics_data.get("healthy_plants", 0),
                    "care_streak_days": analytics_data.get("care_streak_days", 0),
                    "completion_rate": PlantCareFormatter.format_percentage(
                        analytics_data.get("completion_rate", 0)
                    ),
                    "average_health_score": PlantCareFormatter.format_decimal(
                        analytics_data.get("average_health_score", 0), 1
                    )
                },
                "care_statistics": {
                    "tasks_completed_today": analytics_data.get("tasks_completed_today", 0),
                    "tasks_pending": analytics_data.get("tasks_pending", 0),
                    "tasks_overdue": analytics_data.get("tasks_overdue", 0),
                    "most_common_care_type": analytics_data.get("most_common_care_type", "watering"),
                    "weekly_care_frequency": analytics_data.get("weekly_care_frequency", 0)
                },
                "growth_metrics": {
                    "plants_with_photos": analytics_data.get("plants_with_photos", 0),
                    "total_photos": analytics_data.get("total_photos", 0),
                    "growth_milestones": analytics_data.get("growth_milestones", 0),
                    "average_plant_age_days": analytics_data.get("average_plant_age_days", 0)
                },
                "health_insights": {
                    "plants_needing_attention": analytics_data.get("plants_needing_attention", []),
                    "common_issues": analytics_data.get("common_issues", []),
                    "recovery_rate": PlantCareFormatter.format_percentage(
                        analytics_data.get("recovery_rate", 0)
                    )
                },
                "trends": {
                    "care_frequency_trend": analytics_data.get("care_frequency_trend", "stable"),
                    "health_trend": analytics_data.get("health_trend", "stable"),
                    "engagement_trend": analytics_data.get("engagement_trend", "stable")
                },
                "period": {
                    "start_date": PlantCareFormatter.format_datetime(
                        analytics_data.get("period_start"), include_time=False
                    ),
                    "end_date": PlantCareFormatter.format_datetime(
                        analytics_data.get("period_end"), include_time=False
                    ),
                    "days_included": analytics_data.get("days_included", 0)
                }
            }
            
            return analytics
            
        except Exception as e:
            logger.error("Error formatting analytics data", error=str(e))
            return {"error": "Failed to format analytics data"}
    
    @staticmethod
    def format_notification(notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format notification for mobile display.
        
        Args:
            notification_data: Raw notification data
            
        Returns:
            Dict: Formatted notification
        """
        try:
            notification = {
                "notification_id": notification_data.get("notification_id"),
                "type": notification_data.get("type"),
                "title": notification_data.get("title"),
                "message": notification_data.get("message"),
                "icon": PlantCareFormatter.get_notification_icon(
                    notification_data.get("type")
                ),
                "priority": notification_data.get("priority", "normal"),
                "is_read": notification_data.get("is_read", False),
                "action_data": notification_data.get("action_data", {}),
                "plant_info": {
                    "plant_id": notification_data.get("plant_id"),
                    "plant_name": notification_data.get("plant_name"),
                    "thumbnail": notification_data.get("plant_thumbnail")
                } if notification_data.get("plant_id") else None,
                "created_at": PlantCareFormatter.format_datetime(
                    notification_data.get("created_at")
                ),
                "scheduled_for": PlantCareFormatter.format_datetime(
                    notification_data.get("scheduled_for")
                ),
                "delivered_at": PlantCareFormatter.format_datetime(
                    notification_data.get("delivered_at")
                )
            }
            
            # Add time-ago display
            notification["time_ago"] = PlantCareFormatter.format_time_ago(
                notification_data.get("created_at")
            )
            
            return notification
            
        except Exception as e:
            logger.error("Error formatting notification", error=str(e))
            return {"error": "Failed to format notification"}
    
    @staticmethod
    def format_api_response(
        data: Any,
        message: str = "Success",
        status_code: int = 200,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format standardized API response for Plant Care Application.
        
        Args:
            data: Response data
            message: Response message
            status_code: HTTP status code
            metadata: Optional metadata (pagination, etc.)
            
        Returns:
            Dict: Standardized API response
        """
        response = {
            "success": 200 <= status_code < 400,
            "status_code": status_code,
            "message": message,
            "data": data,
            "timestamp": PlantCareFormatter.format_datetime(datetime.utcnow()),
            "api_version": "v1"
        }
        
        if metadata:
            response["metadata"] = metadata
        
        return response
    
    @staticmethod
    def format_error_response(
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400
    ) -> Dict[str, Any]:
        """
        Format standardized error response.
        
        Args:
            error_code: Internal error code
            message: Error message
            details: Optional error details
            status_code: HTTP status code
            
        Returns:
            Dict: Standardized error response
        """
        response = {
            "success": False,
            "status_code": status_code,
            "error": {
                "code": error_code,
                "message": message,
                "details": details or {}
            },
            "timestamp": PlantCareFormatter.format_datetime(datetime.utcnow()),
            "api_version": "v1"
        }
        
        return response
    
    # Helper methods
    @staticmethod
    def calculate_days_owned(acquired_date: Union[datetime, date, str, None]) -> int:
        """Calculate days since plant was acquired."""
        if not acquired_date:
            return 0
        
        try:
            if isinstance(acquired_date, str):
                acquired_dt = datetime.fromisoformat(acquired_date.replace('Z', '+00:00'))
            elif isinstance(acquired_date, date):
                acquired_dt = datetime.combine(acquired_date, datetime.min.time())
            else:
                acquired_dt = acquired_date
            
            delta = datetime.utcnow() - acquired_dt.replace(tzinfo=None)
            return max(0, delta.days)
            
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def format_next_care_date(next_watering: Any, next_fertilizing: Any) -> Dict[str, Any]:
        """Format next care dates for display."""
        result = {
            "watering": PlantCareFormatter.format_datetime(next_watering, include_time=False),
            "fertilizing": PlantCareFormatter.format_datetime(next_fertilizing, include_time=False)
        }
        
        # Determine which care is needed soonest
        dates = [
            (next_watering, "watering"),
            (next_fertilizing, "fertilizing")
        ]
        
        valid_dates = []
        for date_val, care_type in dates:
            if date_val:
                try:
                    if isinstance(date_val, str):
                        parsed_date = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                    else:
                        parsed_date = date_val
                    valid_dates.append((parsed_date, care_type))
                except (ValueError, TypeError):
                    continue
        
        if valid_dates:
            next_date, next_type = min(valid_dates, key=lambda x: x[0])
            result["next_care_type"] = next_type
            result["next_care_date"] = PlantCareFormatter.format_datetime(next_date, include_time=False)
            result["days_until_next_care"] = (next_date.date() - datetime.utcnow().date()).days
        
        return result
    
    @staticmethod
    def calculate_care_urgency(
        next_watering: Any,
        last_watered: Any,
        frequency: str
    ) -> Dict[str, Any]:
        """Calculate care urgency level."""
        urgency = {
            "level": "low",
            "color": "#4CAF50",
            "message": "Care is up to date"
        }
        
        try:
            if next_watering:
                if isinstance(next_watering, str):
                    next_date = datetime.fromisoformat(next_watering.replace('Z', '+00:00'))
                else:
                    next_date = next_watering
                
                days_diff = (next_date.date() - datetime.utcnow().date()).days
                
                if days_diff < 0:  # Overdue
                    urgency.update({
                        "level": "critical",
                        "color": "#F44336",
                        "message": f"Overdue by {abs(days_diff)} day{'s' if abs(days_diff) != 1 else ''}"
                    })
                elif days_diff == 0:  # Due today
                    urgency.update({
                        "level": "high",
                        "color": "#FF9800",
                        "message": "Due today"
                    })
                elif days_diff == 1:  # Due tomorrow
                    urgency.update({
                        "level": "medium",
                        "color": "#FFC107",
                        "message": "Due tomorrow"
                    })
        
        except (ValueError, TypeError):
            pass
        
        return urgency
    
    @staticmethod
    def is_task_overdue(scheduled_date: Any, is_completed: bool) -> bool:
        """Check if a task is overdue."""
        if is_completed or not scheduled_date:
            return False
        
        try:
            if isinstance(scheduled_date, str):
                task_date = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))
            else:
                task_date = scheduled_date
            
            return task_date.date() < datetime.utcnow().date()
            
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def calculate_task_priority(
        scheduled_date: Any,
        care_type: str,
        plant_health: str
    ) -> Dict[str, Any]:
        """Calculate task priority based on multiple factors."""
        priority_score = 3  # Default: medium priority
        
        # Adjust based on care type
        care_priorities = {
            "watering": 5,
            "fertilizing": 3,
            "health_check": 4,
            "pruning": 2,
            "repotting": 2
        }
        priority_score = care_priorities.get(care_type, 3)
        
        # Adjust based on plant health
        health_adjustments = {
            "critical": +2,
            "poor": +1,
            "fair": 0,
            "good": -1,
            "excellent": -1
        }
        priority_score += health_adjustments.get(plant_health, 0)
        
        # Adjust based on how overdue the task is
        if scheduled_date:
            try:
                if isinstance(scheduled_date, str):
                    task_date = datetime.fromisoformat(scheduled_date.replace('Z', '+00:00'))
                else:
                    task_date = scheduled_date
                
                days_overdue = (datetime.utcnow().date() - task_date.date()).days
                if days_overdue > 0:
                    priority_score += min(days_overdue, 3)  # Cap at +3
                    
            except (ValueError, TypeError):
                pass
        
        # Convert score to priority level
        priority_score = max(1, min(priority_score, 5))  # Clamp between 1-5
        
        priority_levels = {
            1: {"level": "very_low", "color": "#E0E0E0", "label": "Very Low"},
            2: {"level": "low", "color": "#4CAF50", "label": "Low"},
            3: {"level": "medium", "color": "#FFC107", "label": "Medium"},
            4: {"level": "high", "color": "#FF9800", "label": "High"},
            5: {"level": "critical", "color": "#F44336", "label": "Critical"}
        }
        
        return priority_levels[priority_score]
    
    @staticmethod
    def format_task_timing(
        scheduled_date: Any,
        completed_date: Any,
        is_completed: bool
    ) -> Dict[str, Any]:
        """Format task timing information."""
        timing = {
            "scheduled_display": None,
            "completed_display": None,
            "status_text": "Pending"
        }
        
        if scheduled_date:
            timing["scheduled_display"] = PlantCareFormatter.format_relative_date(scheduled_date)
        
        if is_completed and completed_date:
            timing["completed_display"] = PlantCareFormatter.format_relative_date(completed_date)
            timing["status_text"] = "Completed"
        elif PlantCareFormatter.is_task_overdue(scheduled_date, is_completed):
            timing["status_text"] = "Overdue"
        
        return timing
    
    @staticmethod
    def format_post_content(content: str, max_length: int = 300) -> str:
        """Format post content for display."""
        if not content:
            return ""
        
        # Basic sanitization
        content = content.strip()
        
        # Truncate if too long
        if len(content) > max_length:
            content = content[:max_length - 3] + "..."
        
        return content
    
    @staticmethod
    def format_time_ago(timestamp: Any) -> str:
        """Format timestamp as 'time ago' string."""
        if not timestamp:
            return "Unknown"
        
        try:
            if isinstance(timestamp, str):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = timestamp
            
            now = datetime.utcnow()
            diff = now - dt.replace(tzinfo=None)
            
            seconds = diff.total_seconds()
            
            if seconds < 60:
                return "Just now"
            elif seconds < 3600:
                minutes = int(seconds // 60)
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif seconds < 86400:
                hours = int(seconds // 3600)
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif seconds < 2592000:  # 30 days
                days = int(seconds // 86400)
                return f"{days} day{'s' if days != 1 else ''} ago"
            elif seconds < 31536000:  # 365 days
                months = int(seconds // 2592000)
                return f"{months} month{'s' if months != 1 else ''} ago"
            else:
                years = int(seconds // 31536000)
                return f"{years} year{'s' if years != 1 else ''} ago"
                
        except (ValueError, TypeError):
            return "Unknown"
    
    @staticmethod
    def format_relative_date(date_input: Any) -> str:
        """Format date relative to today."""
        if not date_input:
            return "Unknown"
        
        try:
            if isinstance(date_input, str):
                dt = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
            else:
                dt = date_input
            
            today = datetime.utcnow().date()
            target_date = dt.date()
            diff = (target_date - today).days
            
            if diff == 0:
                return "Today"
            elif diff == 1:
                return "Tomorrow"
            elif diff == -1:
                return "Yesterday"
            elif diff > 1 and diff <= 7:
                return f"In {diff} days"
            elif diff < -1 and diff >= -7:
                return f"{abs(diff)} days ago"
            else:
                return dt.strftime('%b %d, %Y')
                
        except (ValueError, TypeError):
            return "Unknown"
    
    @staticmethod
    def format_percentage(value: Union[int, float, Decimal, None], decimals: int = 1) -> str:
        """Format percentage value."""
        if value is None:
            return "0.0%"
        
        try:
            percentage = float(value)
            return f"{percentage:.{decimals}f}%"
        except (ValueError, TypeError):
            return "0.0%"
    
    @staticmethod
    def format_decimal(value: Union[int, float, Decimal, None], decimals: int = 2) -> str:
        """Format decimal value."""
        if value is None:
            return "0.00"
        
        try:
            number = float(value)
            return f"{number:.{decimals}f}"
        except (ValueError, TypeError):
            return "0.00"
    
    @staticmethod
    def get_care_type_icon(care_type: str) -> str:
        """Get icon for care type."""
        icons = {
            "watering": "💧",
            "fertilizing": "🌱",
            "pruning": "✂️",
            "repotting": "🪴",
            "rotating": "🔄",
            "misting": "💨",
            "cleaning": "🧽",
            "checking": "👀",
            "harvesting": "🌾"
        }
        return icons.get(care_type, "🌿")
    
    @staticmethod
    def get_notification_icon(notification_type: str) -> str:
        """Get icon for notification type."""
        icons = {
            "care_reminder": "⏰",
            "health_alert": "🚨",
            "milestone": "🎉",
            "community": "👥",
            "system": "⚙️",
            "marketing": "📢",
            "weather": "🌤️",
            "expert_advice": "👨‍🌾"
        }
        return icons.get(notification_type, "📱")


# Convenience functions for common formatting operations
def format_plant_for_api(plant_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format plant data for API response."""
    return PlantCareFormatter.format_plant_summary(plant_data)


def format_care_tasks_for_api(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format list of care tasks for API response."""
    return [PlantCareFormatter.format_care_task(task) for task in tasks]


def format_success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Format successful API response."""
    return PlantCareFormatter.format_api_response(data, message, 200)


def format_error_response(error_code: str, message: str, status_code: int = 400) -> Dict[str, Any]:
    """Format error API response."""
    return PlantCareFormatter.format_error_response(error_code, message, None, status_code)


def format_pagination_metadata(
    total_items: int,
    page: int,
    page_size: int,
    total_pages: int
) -> Dict[str, Any]:
    """Format pagination metadata."""
    return {
        "pagination": {
            "total_items": total_items,
            "current_page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next_page": page < total_pages,
            "has_previous_page": page > 1,
            "next_page": page + 1 if page < total_pages else None,
            "previous_page": page - 1 if page > 1 else None
        }
    }