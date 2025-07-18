"""
app/shared/utils/validators.py
Plant Care Application - Input Validators

Validation utilities for Plant Care Application data including plant data,
care schedules, health records, and user inputs.
"""
import re
import uuid
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from email_validator import validate_email, EmailNotValidError
import structlog

from app.shared.config.settings import get_settings
from app.shared.core.exceptions import ValidationError

# Setup logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()


class PlantCareValidator:
    """
    Comprehensive validator for Plant Care Application data.
    """
    
    # Plant care specific validation rules
    VALID_CARE_TYPES = {
        "watering", "fertilizing", "pruning", "repotting", "rotating",
        "misting", "cleaning", "checking", "harvesting"
    }
    
    VALID_HEALTH_STATUSES = {
        "excellent", "good", "fair", "poor", "critical", "recovering", "unknown"
    }
    
    VALID_GROWTH_STAGES = {
        "seed", "seedling", "vegetative", "flowering", "fruiting", "dormant", "mature"
    }
    
    VALID_PLANT_CATEGORIES = {
        "houseplant", "outdoor", "succulent", "herb", "vegetable", "flower",
        "tree", "shrub", "vine", "fern", "orchid", "cactus"
    }
    
    VALID_LIGHT_REQUIREMENTS = {
        "low", "medium", "bright", "direct", "indirect", "partial", "full_sun", "shade"
    }
    
    VALID_WATER_FREQUENCIES = {
        "daily", "every_2_days", "every_3_days", "weekly", "bi_weekly",
        "monthly", "seasonal", "as_needed"
    }
    
    VALID_SUBSCRIPTION_PLANS = {
        "free", "premium_monthly", "premium_yearly", "expert", "family"
    }
    
    VALID_NOTIFICATION_TYPES = {
        "care_reminder", "health_alert", "milestone", "community", "system",
        "marketing", "weather", "expert_advice"
    }
    
    VALID_FILE_EXTENSIONS = {
        "image": {".jpg", ".jpeg", ".png", ".webp", ".heic"},
        "document": {".pdf", ".doc", ".docx", ".txt"},
        "video": {".mp4", ".mov", ".avi"}
    }
    
    # Size limits (in bytes)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DOCUMENT_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email address format for Plant Care users.
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if email is valid
            
        Raises:
            ValidationError: If email is invalid
        """
        try:
            # Use email-validator library for comprehensive validation
            validated_email = validate_email(email)
            normalized_email = validated_email.email
            
            # Additional Plant Care specific checks
            if len(normalized_email) > 254:
                raise ValidationError(
                    message="Email address is too long",
                    details={"email": email, "max_length": 254}
                )
            
            # Check for disposable email domains (basic list)
            disposable_domains = {
                "10minutemail.com", "tempmail.org", "guerrillamail.com",
                "mailinator.com", "throwaway.email"
            }
            
            domain = normalized_email.split("@")[1].lower()
            if domain in disposable_domains:
                raise ValidationError(
                    message="Disposable email addresses are not allowed",
                    details={"email": email, "domain": domain}
                )
            
            logger.debug("Email validated successfully", email=normalized_email)
            return True
            
        except EmailNotValidError as e:
            logger.warning("Email validation failed", email=email, error=str(e))
            raise ValidationError(
                message="Invalid email address format",
                details={"email": email, "error": str(e)}
            )
    
    @staticmethod
    def validate_password(password: str) -> bool:
        """
        Validate password strength for Plant Care users.
        
        Args:
            password: Password to validate
            
        Returns:
            bool: True if password is valid
            
        Raises:
            ValidationError: If password doesn't meet requirements
        """
        errors = []
        
        # Length check
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if len(password) > 128:
            errors.append("Password must not exceed 128 characters")
        
        # Character requirements
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Common password patterns
        common_patterns = [
            r'(.)\1{2,}',  # Repeated characters (aaa, 111)
            r'123456',     # Sequential numbers
            r'abcdef',     # Sequential letters
            r'qwerty',     # Keyboard patterns
            r'password',   # Common words
            r'plant',      # App-specific words
            r'garden',
        ]
        
        for pattern in common_patterns:
            if re.search(pattern, password.lower()):
                errors.append(f"Password contains common patterns and is not secure")
                break
        
        if errors:
            raise ValidationError(
                message="Password does not meet security requirements",
                details={"errors": errors}
            )
        
        return True
    
    @staticmethod
    def validate_plant_name(name: str) -> bool:
        """
        Validate plant name for Plant Care Application.
        
        Args:
            name: Plant name to validate
            
        Returns:
            bool: True if name is valid
            
        Raises:
            ValidationError: If name is invalid
        """
        if not name or not name.strip():
            raise ValidationError(
                message="Plant name is required",
                details={"field": "name"}
            )
        
        name = name.strip()
        
        if len(name) < 1:
            raise ValidationError(
                message="Plant name must be at least 1 character long",
                details={"name": name, "min_length": 1}
            )
        
        if len(name) > 100:
            raise ValidationError(
                message="Plant name must not exceed 100 characters",
                details={"name": name, "max_length": 100}
            )
        
        # Check for valid characters (letters, numbers, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z0-9\s\-']+$", name):
            raise ValidationError(
                message="Plant name contains invalid characters",
                details={"name": name, "allowed_chars": "letters, numbers, spaces, hyphens, apostrophes"}
            )
        
        return True
    
    @staticmethod
    def validate_care_schedule(care_data: Dict[str, Any]) -> bool:
        """
        Validate care schedule data.
        
        Args:
            care_data: Care schedule data to validate
            
        Returns:
            bool: True if schedule is valid
            
        Raises:
            ValidationError: If schedule data is invalid
        """
        required_fields = ["care_type", "frequency", "plant_id"]
        
        for field in required_fields:
            if field not in care_data:
                raise ValidationError(
                    message=f"Required field '{field}' is missing",
                    details={"missing_field": field, "required_fields": required_fields}
                )
        
        # Validate care type
        care_type = care_data["care_type"].lower()
        if care_type not in PlantCareValidator.VALID_CARE_TYPES:
            raise ValidationError(
                message="Invalid care type",
                details={
                    "care_type": care_type,
                    "valid_types": list(PlantCareValidator.VALID_CARE_TYPES)
                }
            )
        
        # Validate frequency
        frequency = care_data["frequency"]
        if frequency not in PlantCareValidator.VALID_WATER_FREQUENCIES:
            raise ValidationError(
                message="Invalid care frequency",
                details={
                    "frequency": frequency,
                    "valid_frequencies": list(PlantCareValidator.VALID_WATER_FREQUENCIES)
                }
            )
        
        # Validate plant ID
        PlantCareValidator.validate_uuid(care_data["plant_id"])
        
        # Validate optional fields
        if "start_date" in care_data:
            PlantCareValidator.validate_date(care_data["start_date"])
        
        if "notes" in care_data:
            notes = care_data["notes"]
            if len(notes) > 500:
                raise ValidationError(
                    message="Care notes must not exceed 500 characters",
                    details={"notes_length": len(notes), "max_length": 500}
                )
        
        return True
    
    @staticmethod
    def validate_health_record(health_data: Dict[str, Any]) -> bool:
        """
        Validate plant health record data.
        
        Args:
            health_data: Health record data to validate
            
        Returns:
            bool: True if health data is valid
            
        Raises:
            ValidationError: If health data is invalid
        """
        required_fields = ["plant_id", "health_status", "recorded_date"]
        
        for field in required_fields:
            if field not in health_data:
                raise ValidationError(
                    message=f"Required field '{field}' is missing",
                    details={"missing_field": field}
                )
        
        # Validate plant ID
        PlantCareValidator.validate_uuid(health_data["plant_id"])
        
        # Validate health status
        health_status = health_data["health_status"].lower()
        if health_status not in PlantCareValidator.VALID_HEALTH_STATUSES:
            raise ValidationError(
                message="Invalid health status",
                details={
                    "health_status": health_status,
                    "valid_statuses": list(PlantCareValidator.VALID_HEALTH_STATUSES)
                }
            )
        
        # Validate recorded date
        PlantCareValidator.validate_date(health_data["recorded_date"])
        
        # Validate optional fields
        if "symptoms" in health_data:
            symptoms = health_data["symptoms"]
            if isinstance(symptoms, list):
                for symptom in symptoms:
                    if not isinstance(symptom, str) or len(symptom) > 100:
                        raise ValidationError(
                            message="Each symptom must be a string with max 100 characters",
                            details={"symptom": symptom}
                        )
            else:
                raise ValidationError(
                    message="Symptoms must be a list of strings",
                    details={"symptoms_type": type(symptoms)}
                )
        
        if "severity" in health_data:
            severity = health_data["severity"]
            valid_severities = {"low", "medium", "high", "critical"}
            if severity not in valid_severities:
                raise ValidationError(
                    message="Invalid severity level",
                    details={"severity": severity, "valid_severities": list(valid_severities)}
                )
        
        return True
    
    @staticmethod
    def validate_uuid(uuid_string: str, field_name: str = "ID") -> bool:
        """
        Validate UUID format.
        
        Args:
            uuid_string: UUID string to validate
            field_name: Name of the field for error messages
            
        Returns:
            bool: True if UUID is valid
            
        Raises:
            ValidationError: If UUID is invalid
        """
        try:
            uuid.UUID(uuid_string, version=4)
            return True
        except (ValueError, TypeError):
            raise ValidationError(
                message=f"Invalid {field_name} format",
                details={"field": field_name, "value": uuid_string, "expected_format": "UUID v4"}
            )
    
    @staticmethod
    def validate_date(date_input: Union[str, datetime, date]) -> bool:
        """
        Validate date format and range.
        
        Args:
            date_input: Date to validate (string, datetime, or date object)
            
        Returns:
            bool: True if date is valid
            
        Raises:
            ValidationError: If date is invalid
        """
        try:
            if isinstance(date_input, str):
                # Try parsing ISO format first
                try:
                    parsed_date = datetime.fromisoformat(date_input.replace('Z', '+00:00'))
                except ValueError:
                    # Try parsing date only
                    parsed_date = datetime.strptime(date_input, '%Y-%m-%d')
            elif isinstance(date_input, datetime):
                parsed_date = date_input
            elif isinstance(date_input, date):
                parsed_date = datetime.combine(date_input, datetime.min.time())
            else:
                raise ValidationError(
                    message="Invalid date format",
                    details={"date_input": str(date_input), "type": type(date_input)}
                )
            
            # Check if date is reasonable (not too far in past or future)
            now = datetime.now()
            min_date = now - timedelta(days=365 * 10)  # 10 years ago
            max_date = now + timedelta(days=365 * 2)   # 2 years from now
            
            if parsed_date < min_date:
                raise ValidationError(
                    message="Date is too far in the past",
                    details={"date": parsed_date.isoformat(), "min_date": min_date.isoformat()}
                )
            
            if parsed_date > max_date:
                raise ValidationError(
                    message="Date is too far in the future",
                    details={"date": parsed_date.isoformat(), "max_date": max_date.isoformat()}
                )
            
            return True
            
        except ValueError as e:
            raise ValidationError(
                message="Invalid date format",
                details={"date_input": str(date_input), "error": str(e)}
            )
    
    @staticmethod
    def validate_file_upload(file_data: Dict[str, Any]) -> bool:
        """
        Validate file upload data for Plant Care Application.
        
        Args:
            file_data: File data including filename, size, content_type
            
        Returns:
            bool: True if file is valid
            
        Raises:
            ValidationError: If file is invalid
        """
        required_fields = ["filename", "size", "content_type"]
        
        for field in required_fields:
            if field not in file_data:
                raise ValidationError(
                    message=f"Required field '{field}' is missing",
                    details={"missing_field": field}
                )
        
        filename = file_data["filename"]
        file_size = file_data["size"]
        content_type = file_data["content_type"]
        
        # Validate filename
        if not filename or len(filename) < 1:
            raise ValidationError(
                message="Filename is required",
                details={"filename": filename}
            )
        
        if len(filename) > 255:
            raise ValidationError(
                message="Filename is too long",
                details={"filename": filename, "max_length": 255}
            )
        
        # Get file extension
        file_extension = "." + filename.split(".")[-1].lower() if "." in filename else ""
        
        # Determine file type and validate
        if content_type.startswith("image/"):
            if file_extension not in PlantCareValidator.VALID_FILE_EXTENSIONS["image"]:
                raise ValidationError(
                    message="Invalid image file extension",
                    details={
                        "extension": file_extension,
                        "valid_extensions": list(PlantCareValidator.VALID_FILE_EXTENSIONS["image"])
                    }
                )
            
            if file_size > PlantCareValidator.MAX_IMAGE_SIZE:
                raise ValidationError(
                    message="Image file is too large",
                    details={
                        "file_size": file_size,
                        "max_size": PlantCareValidator.MAX_IMAGE_SIZE,
                        "max_size_mb": PlantCareValidator.MAX_IMAGE_SIZE / (1024 * 1024)
                    }
                )
        
        elif content_type.startswith("video/"):
            if file_extension not in PlantCareValidator.VALID_FILE_EXTENSIONS["video"]:
                raise ValidationError(
                    message="Invalid video file extension",
                    details={
                        "extension": file_extension,
                        "valid_extensions": list(PlantCareValidator.VALID_FILE_EXTENSIONS["video"])
                    }
                )
            
            if file_size > PlantCareValidator.MAX_VIDEO_SIZE:
                raise ValidationError(
                    message="Video file is too large",
                    details={
                        "file_size": file_size,
                        "max_size": PlantCareValidator.MAX_VIDEO_SIZE,
                        "max_size_mb": PlantCareValidator.MAX_VIDEO_SIZE / (1024 * 1024)
                    }
                )
        
        else:
            # Assume document
            if file_extension not in PlantCareValidator.VALID_FILE_EXTENSIONS["document"]:
                raise ValidationError(
                    message="Invalid document file extension",
                    details={
                        "extension": file_extension,
                        "valid_extensions": list(PlantCareValidator.VALID_FILE_EXTENSIONS["document"])
                    }
                )
            
            if file_size > PlantCareValidator.MAX_DOCUMENT_SIZE:
                raise ValidationError(
                    message="Document file is too large",
                    details={
                        "file_size": file_size,
                        "max_size": PlantCareValidator.MAX_DOCUMENT_SIZE,
                        "max_size_mb": PlantCareValidator.MAX_DOCUMENT_SIZE / (1024 * 1024)
                    }
                )
        
        return True
    
    @staticmethod
    def validate_community_post(post_data: Dict[str, Any]) -> bool:
        """
        Validate community post data.
        
        Args:
            post_data: Community post data to validate
            
        Returns:
            bool: True if post is valid
            
        Raises:
            ValidationError: If post data is invalid
        """
        required_fields = ["title", "content", "author_id"]
        
        for field in required_fields:
            if field not in post_data:
                raise ValidationError(
                    message=f"Required field '{field}' is missing",
                    details={"missing_field": field}
                )
        
        # Validate title
        title = post_data["title"].strip()
        if len(title) < 5:
            raise ValidationError(
                message="Post title must be at least 5 characters long",
                details={"title": title, "min_length": 5}
            )
        
        if len(title) > 200:
            raise ValidationError(
                message="Post title must not exceed 200 characters",
                details={"title": title, "max_length": 200}
            )
        
        # Validate content
        content = post_data["content"].strip()
        if len(content) < 10:
            raise ValidationError(
                message="Post content must be at least 10 characters long",
                details={"content_length": len(content), "min_length": 10}
            )
        
        if len(content) > 5000:
            raise ValidationError(
                message="Post content must not exceed 5000 characters",
                details={"content_length": len(content), "max_length": 5000}
            )
        
        # Validate author ID
        PlantCareValidator.validate_uuid(post_data["author_id"], "author_id")
        
        # Validate optional tags
        if "tags" in post_data:
            tags = post_data["tags"]
            if not isinstance(tags, list):
                raise ValidationError(
                    message="Tags must be a list",
                    details={"tags_type": type(tags)}
                )
            
            if len(tags) > 10:
                raise ValidationError(
                    message="Maximum 10 tags allowed",
                    details={"tags_count": len(tags), "max_tags": 10}
                )
            
            for tag in tags:
                if not isinstance(tag, str) or len(tag) > 30:
                    raise ValidationError(
                        message="Each tag must be a string with max 30 characters",
                        details={"tag": tag}
                    )
        
        return True
    
    @staticmethod
    def validate_search_query(query: str) -> str:
        """
        Validate and sanitize search query.
        
        Args:
            query: Search query string
            
        Returns:
            str: Sanitized query
            
        Raises:
            ValidationError: If query is invalid
        """
        if not query or not query.strip():
            raise ValidationError(
                message="Search query cannot be empty",
                details={"query": query}
            )
        
        query = query.strip()
        
        if len(query) < 2:
            raise ValidationError(
                message="Search query must be at least 2 characters long",
                details={"query": query, "min_length": 2}
            )
        
        if len(query) > 200:
            raise ValidationError(
                message="Search query must not exceed 200 characters",
                details={"query": query, "max_length": 200}
            )
        
        # Remove potentially harmful characters
        sanitized_query = re.sub(r'[<>"\']', '', query)
        
        if sanitized_query != query:
            logger.warning(
                "Search query sanitized",
                original_query=query,
                sanitized_query=sanitized_query
            )
        
        return sanitized_query


# Convenience validation functions
def validate_email_address(email: str) -> bool:
    """Validate email address."""
    return PlantCareValidator.validate_email(email)


def validate_password_strength(password: str) -> bool:
    """Validate password strength."""
    return PlantCareValidator.validate_password(password)


def validate_plant_data(plant_data: Dict[str, Any]) -> bool:
    """
    Validate comprehensive plant data.
    
    Args:
        plant_data: Plant data to validate
        
    Returns:
        bool: True if all data is valid
    """
    # Validate required fields
    if "name" in plant_data:
        PlantCareValidator.validate_plant_name(plant_data["name"])
    
    if "user_id" in plant_data:
        PlantCareValidator.validate_uuid(plant_data["user_id"], "user_id")
    
    # Validate optional fields
    if "species" in plant_data and plant_data["species"]:
        PlantCareValidator.validate_plant_name(plant_data["species"])
    
    if "category" in plant_data:
        category = plant_data["category"].lower()
        if category not in PlantCareValidator.VALID_PLANT_CATEGORIES:
            raise ValidationError(
                message="Invalid plant category",
                details={
                    "category": category,
                    "valid_categories": list(PlantCareValidator.VALID_PLANT_CATEGORIES)
                }
            )
    
    if "light_requirement" in plant_data:
        light = plant_data["light_requirement"].lower()
        if light not in PlantCareValidator.VALID_LIGHT_REQUIREMENTS:
            raise ValidationError(
                message="Invalid light requirement",
                details={
                    "light_requirement": light,
                    "valid_requirements": list(PlantCareValidator.VALID_LIGHT_REQUIREMENTS)
                }
            )
    
    if "acquired_date" in plant_data:
        PlantCareValidator.validate_date(plant_data["acquired_date"])
    
    return True


def validate_user_profile(profile_data: Dict[str, Any]) -> bool:
    """
    Validate user profile data.
    
    Args:
        profile_data: User profile data to validate
        
    Returns:
        bool: True if profile is valid
    """
    if "email" in profile_data:
        PlantCareValidator.validate_email(profile_data["email"])
    
    if "user_id" in profile_data:
        PlantCareValidator.validate_uuid(profile_data["user_id"], "user_id")
    
    if "subscription_plan" in profile_data:
        plan = profile_data["subscription_plan"]
        if plan not in PlantCareValidator.VALID_SUBSCRIPTION_PLANS:
            raise ValidationError(
                message="Invalid subscription plan",
                details={
                    "plan": plan,
                    "valid_plans": list(PlantCareValidator.VALID_SUBSCRIPTION_PLANS)
                }
            )
    
    if "notification_preferences" in profile_data:
        prefs = profile_data["notification_preferences"]
        if not isinstance(prefs, dict):
            raise ValidationError(
                message="Notification preferences must be a dictionary",
                details={"prefs_type": type(prefs)}
            )
        
        for notif_type, enabled in prefs.items():
            if notif_type not in PlantCareValidator.VALID_NOTIFICATION_TYPES:
                raise ValidationError(
                    message="Invalid notification type",
                    details={
                        "notification_type": notif_type,
                        "valid_types": list(PlantCareValidator.VALID_NOTIFICATION_TYPES)
                    }
                )
            
            if not isinstance(enabled, bool):
                raise ValidationError(
                    message="Notification preference must be boolean",
                    details={"notification_type": notif_type, "value": enabled}
                )
    
    return True

# Standalone pagination validator for import
def validate_pagination_params(page: int, size: int) -> Tuple[int, int]:
    """
    Validate and normalize pagination parameters.

    Args:
        page: Page number (1-based)
        size: Page size

    Returns:
        Tuple[int, int]: Validated (page, size)

    Raises:
        ValidationError: If parameters are invalid
    """
    if page < 1:
        raise ValidationError(
            message="Page number must be 1 or greater",
            details={"page": page, "min_page": 1}
        )

    if page > 10000:
        raise ValidationError(
            message="Page number is too large",
            details={"page": page, "max_page": 10000}
        )

    if size < 1:
        raise ValidationError(
            message="Page size must be 1 or greater",
            details={"size": size, "min_size": 1}
        )

    if size > 100:
        logger.warning(
            "Page size limited to maximum",
            requested_size=size,
            max_size=100
        )
        size = 100

    return page, size