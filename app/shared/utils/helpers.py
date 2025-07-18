"""
app/shared/utils/helpers.py
Plant Care Application - Utility Helper Functions

Common utility functions for Plant Care Application including text processing,
image utilities, calculation helpers, and general purpose functions.
"""
import re
import hashlib
import secrets
import base64
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
import math
import structlog

from app.shared.config.settings import get_settings

# Setup logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()


class PlantCareHelpers:
    """
    Utility helper functions for Plant Care Application.
    """
    
    @staticmethod
    def generate_unique_id(prefix: str = "", length: int = 8) -> str:
        """
        Generate unique ID for Plant Care entities.
        
        Args:
            prefix: Optional prefix for the ID
            length: Length of random part
            
        Returns:
            str: Unique ID
        """
        random_part = secrets.token_hex(length // 2)
        if prefix:
            return f"{prefix}_{random_part}"
        return random_part
    
    @staticmethod
    def generate_plant_id() -> str:
        """Generate unique plant ID."""
        return PlantCareHelpers.generate_unique_id("plant", 12)
    
    @staticmethod
    def generate_care_task_id() -> str:
        """Generate unique care task ID."""
        return PlantCareHelpers.generate_unique_id("task", 10)
    
    @staticmethod
    def generate_user_slug(display_name: str, user_id: str) -> str:
        """
        Generate URL-friendly slug for user profiles.
        
        Args:
            display_name: User's display name
            user_id: User's unique ID
            
        Returns:
            str: URL-friendly slug
        """
        if not display_name:
            return f"user-{user_id[:8]}"
        
        # Clean and normalize the display name
        slug = display_name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)  # Remove special chars
        slug = re.sub(r'[-\s]+', '-', slug)   # Replace spaces/hyphens with single hyphen
        slug = slug.strip('-')                # Remove leading/trailing hyphens
        
        # Truncate if too long
        if len(slug) > 30:
            slug = slug[:30].rstrip('-')
        
        # Add user ID suffix to ensure uniqueness
        return f"{slug}-{user_id[:6]}" if slug else f"user-{user_id[:8]}"
    
    @staticmethod
    def clean_plant_name(name: str) -> str:
        """
        Clean and normalize plant name.
        
        Args:
            name: Raw plant name
            
        Returns:
            str: Cleaned plant name
        """
        if not name:
            return ""
        
        # Basic cleaning
        cleaned = name.strip()
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Capitalize first letter of each word (title case)
        cleaned = cleaned.title()
        
        # Handle common plant name patterns
        # e.g., "spider plant (variegated)" -> "Spider Plant (Variegated)"
        cleaned = re.sub(r'\(([^)]+)\)', lambda m: f"({m.group(1).title()})", cleaned)
        
        return cleaned
    
    @staticmethod
    def extract_species_from_name(full_name: str) -> Tuple[str, Optional[str]]:
        """
        Extract plant name and species from full name.
        
        Args:
            full_name: Full plant name potentially containing species
            
        Returns:
            Tuple[str, Optional[str]]: (common_name, species)
        """
        if not full_name:
            return "", None
        
        # Common patterns for species names
        # "Spider Plant (Chlorophytum comosum)"
        species_match = re.search(r'\(([A-Z][a-z]+ [a-z]+)\)', full_name)
        if species_match:
            species = species_match.group(1)
            common_name = full_name.replace(species_match.group(0), '').strip()
            return PlantCareHelpers.clean_plant_name(common_name), species
        
        # "Chlorophytum comosum - Spider Plant"
        if ' - ' in full_name:
            parts = full_name.split(' - ')
            if len(parts) == 2:
                if re.match(r'^[A-Z][a-z]+ [a-z]+', parts[0].strip()):
                    return PlantCareHelpers.clean_plant_name(parts[1]), parts[0].strip()
                else:
                    return PlantCareHelpers.clean_plant_name(parts[0]), parts[1].strip()
        
        return PlantCareHelpers.clean_plant_name(full_name), None
    
    @staticmethod
    def calculate_next_care_date(
        last_care_date: Union[datetime, date, str],
        frequency: str,
        timezone_offset: int = 0
    ) -> datetime:
        """
        Calculate next care date based on frequency.
        
        Args:
            last_care_date: Last care date
            frequency: Care frequency code
            timezone_offset: Timezone offset in hours
            
        Returns:
            datetime: Next care date
        """
        try:
            # Parse last care date
            if isinstance(last_care_date, str):
                base_date = datetime.fromisoformat(last_care_date.replace('Z', '+00:00'))
            elif isinstance(last_care_date, date):
                base_date = datetime.combine(last_care_date, datetime.min.time())
            else:
                base_date = last_care_date
            
            # Apply timezone offset
            base_date = base_date + timedelta(hours=timezone_offset)
            
            # Calculate days to add based on frequency
            frequency_days = {
                "daily": 1,
                "every_2_days": 2,
                "every_3_days": 3,
                "weekly": 7,
                "bi_weekly": 14,
                "monthly": 30,
                "seasonal": 90,
                "as_needed": 365  # Default to yearly for "as needed"
            }
            
            days_to_add = frequency_days.get(frequency, 7)  # Default to weekly
            next_date = base_date + timedelta(days=days_to_add)
            
            return next_date
            
        except (ValueError, TypeError) as e:
            logger.error("Error calculating next care date", error=str(e))
            return datetime.utcnow() + timedelta(days=7)  # Default to 7 days from now
    
    @staticmethod
    def calculate_plant_age(acquired_date: Union[datetime, date, str]) -> Dict[str, int]:
        """
        Calculate plant age in various units.
        
        Args:
            acquired_date: Date plant was acquired
            
        Returns:
            Dict: Age in days, weeks, months, years
        """
        try:
            if isinstance(acquired_date, str):
                acquired_dt = datetime.fromisoformat(acquired_date.replace('Z', '+00:00'))
            elif isinstance(acquired_date, date):
                acquired_dt = datetime.combine(acquired_date, datetime.min.time())
            else:
                acquired_dt = acquired_date
            
            now = datetime.utcnow()
            delta = now - acquired_dt.replace(tzinfo=None)
            
            days = delta.days
            weeks = days // 7
            months = days // 30
            years = days // 365
            
            return {
                "days": days,
                "weeks": weeks,
                "months": months,
                "years": years
            }
            
        except (ValueError, TypeError):
            return {"days": 0, "weeks": 0, "months": 0, "years": 0}
    
    @staticmethod
    def calculate_care_score(
        tasks_completed: int,
        tasks_scheduled: int,
        health_status: str,
        consistency_bonus: float = 0.0
    ) -> float:
        """
        Calculate plant care score (0-100).
        
        Args:
            tasks_completed: Number of completed care tasks
            tasks_scheduled: Number of scheduled care tasks
            health_status: Current health status
            consistency_bonus: Bonus for consistency (0-1)
            
        Returns:
            float: Care score (0-100)
        """
        if tasks_scheduled == 0:
            base_score = 50  # Neutral score if no tasks
        else:
            completion_rate = tasks_completed / tasks_scheduled
            base_score = completion_rate * 60  # Max 60 points for completion
        
        # Health status bonus
        health_bonus = {
            "excellent": 25,
            "good": 20,
            "fair": 10,
            "poor": 5,
            "critical": 0,
            "recovering": 15,
            "unknown": 10
        }.get(health_status, 10)
        
        # Consistency bonus (max 15 points)
        consistency_points = consistency_bonus * 15
        
        total_score = base_score + health_bonus + consistency_points
        return min(100, max(0, round(total_score, 1)))
    
    @staticmethod
    def calculate_watering_amount(
        plant_size: str,
        pot_size: str,
        season: str,
        humidity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate recommended watering amount.
        
        Args:
            plant_size: Size of plant (small, medium, large)
            pot_size: Size of pot (small, medium, large)
            season: Current season
            humidity: Optional humidity percentage
            
        Returns:
            Dict: Watering recommendations
        """
        # Base amounts in milliliters
        base_amounts = {
            ("small", "small"): 50,
            ("small", "medium"): 75,
            ("small", "large"): 100,
            ("medium", "small"): 100,
            ("medium", "medium"): 150,
            ("medium", "large"): 200,
            ("large", "small"): 150,
            ("large", "medium"): 250,
            ("large", "large"): 350
        }
        
        base_amount = base_amounts.get((plant_size, pot_size), 150)
        
        # Seasonal adjustments
        seasonal_multipliers = {
            "spring": 1.2,
            "summer": 1.4,
            "fall": 0.9,
            "winter": 0.7
        }
        
        multiplier = seasonal_multipliers.get(season, 1.0)
        
        # Humidity adjustments
        if humidity is not None:
            if humidity > 70:
                multiplier *= 0.8  # Less water in high humidity
            elif humidity < 30:
                multiplier *= 1.3  # More water in low humidity
        
        recommended_amount = int(base_amount * multiplier)
        
        return {
            "amount_ml": recommended_amount,
            "amount_cups": round(recommended_amount / 240, 2),  # 1 cup = 240ml
            "description": PlantCareHelpers.get_watering_description(recommended_amount),
            "frequency_adjustment": PlantCareHelpers.get_frequency_adjustment(season, humidity)
        }
    
    @staticmethod
    def get_watering_description(amount_ml: int) -> str:
        """Get human-readable watering description."""
        if amount_ml < 100:
            return "Light watering - just a splash"
        elif amount_ml < 200:
            return "Moderate watering - a small cup"
        elif amount_ml < 350:
            return "Generous watering - a full cup"
        else:
            return "Deep watering - multiple cups"
    
    @staticmethod
    def get_frequency_adjustment(season: str, humidity: Optional[float]) -> str:
        """Get frequency adjustment recommendation."""
        adjustments = []
        
        if season == "summer":
            adjustments.append("water more frequently in summer heat")
        elif season == "winter":
            adjustments.append("water less frequently in winter")
        
        if humidity is not None:
            if humidity > 70:
                adjustments.append("reduce frequency in high humidity")
            elif humidity < 30:
                adjustments.append("increase frequency in dry conditions")
        
        return "; ".join(adjustments) if adjustments else "maintain regular schedule"
    
    @staticmethod
    def generate_care_reminder_message(
        plant_name: str,
        care_type: str,
        days_overdue: int = 0
    ) -> str:
        """
        Generate personalized care reminder message.
        
        Args:
            plant_name: Name of the plant
            care_type: Type of care needed
            days_overdue: Number of days overdue
            
        Returns:
            str: Personalized reminder message
        """
        care_messages = {
            "watering": [
                f"💧 {plant_name} is thirsty! Time for watering.",
                f"🌿 {plant_name} needs a drink. Don't forget to water!",
                f"💦 Your {plant_name} is asking for water.",
                f"🪴 Time to hydrate {plant_name}!"
            ],
            "fertilizing": [
                f"🌱 {plant_name} could use some nutrients. Time to fertilize!",
                f"🍃 Give {plant_name} a nutritional boost with fertilizer.",
                f"🌿 {plant_name} is ready for feeding time!",
                f"💚 Help {plant_name} grow strong with fertilizer."
            ],
            "pruning": [
                f"✂️ {plant_name} needs a little trim. Time for pruning!",
                f"🌿 Give {plant_name} a fresh look with some pruning.",
                f"🌱 {plant_name} will appreciate a good pruning session.",
                f"✨ Shape up {plant_name} with some careful pruning."
            ],
            "health_check": [
                f"👀 Time to check on {plant_name}'s health!",
                f"🔍 Give {plant_name} a thorough health inspection.",
                f"💚 How is {plant_name} doing today? Time for a check-up!",
                f"🌿 Monitor {plant_name}'s wellbeing with a health check."
            ]
        }
        
        messages = care_messages.get(care_type, [f"🌿 {plant_name} needs some {care_type}."])
        base_message = secrets.choice(messages)
        
        if days_overdue > 0:
            if days_overdue == 1:
                base_message += f" (1 day overdue)"
            else:
                base_message += f" ({days_overdue} days overdue)"
        
        return base_message
    
    @staticmethod
    def extract_hashtags(text: str) -> List[str]:
        """
        Extract hashtags from text.
        
        Args:
            text: Text to extract hashtags from
            
        Returns:
            List[str]: List of hashtags without # symbol
        """
        if not text:
            return []
        
        hashtag_pattern = r'#(\w+)'
        hashtags = re.findall(hashtag_pattern, text, re.IGNORECASE)
        
        # Clean and deduplicate
        cleaned_hashtags = []
        for tag in hashtags:
            tag = tag.lower().strip()
            if tag and len(tag) > 1 and tag not in cleaned_hashtags:
                cleaned_hashtags.append(tag)
        
        return cleaned_hashtags
    
    @staticmethod
    def extract_mentions(text: str) -> List[str]:
        """
        Extract user mentions from text.
        
        Args:
            text: Text to extract mentions from
            
        Returns:
            List[str]: List of mentioned usernames without @ symbol
        """
        if not text:
            return []
        
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, text, re.IGNORECASE)
        
        # Clean and deduplicate
        cleaned_mentions = []
        for mention in mentions:
            mention = mention.lower().strip()
            if mention and len(mention) > 1 and mention not in cleaned_mentions:
                cleaned_mentions.append(mention)
        
        return cleaned_mentions
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for safe storage.
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        if not filename:
            return "unnamed_file"
        
        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]
        
        # Replace unsafe characters
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Remove multiple consecutive underscores
        filename = re.sub(r'_{2,}', '_', filename)
        
        # Ensure it doesn't start with a dot
        filename = filename.lstrip('.')
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_length = 255 - len(ext) - 1 if ext else 255
            filename = name[:max_name_length] + ('.' + ext if ext else '')
        
        return filename or "unnamed_file"
    
    @staticmethod
    def generate_thumbnail_filename(original_filename: str, size: str = "thumb") -> str:
        """
        Generate thumbnail filename from original.
        
        Args:
            original_filename: Original file name
            size: Thumbnail size identifier
            
        Returns:
            str: Thumbnail filename
        """
        name, ext = original_filename.rsplit('.', 1) if '.' in original_filename else (original_filename, 'jpg')
        timestamp = int(datetime.utcnow().timestamp())
        return f"{name}_{size}_{timestamp}.{ext}"
    
    @staticmethod
    def create_file_hash(file_content: bytes) -> str:
        """
        Create hash of file content for deduplication.
        
        Args:
            file_content: File content as bytes
            
        Returns:
            str: SHA-256 hash of file content
        """
        return hashlib.sha256(file_content).hexdigest()
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            str: Formatted size string
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {size_names[i]}"
    
    @staticmethod
    def calculate_image_resize_dimensions(
        original_width: int,
        original_height: int,
        max_width: int,
        max_height: int,
        maintain_aspect: bool = True
    ) -> Tuple[int, int]:
        """
        Calculate new dimensions for image resizing.
        
        Args:
            original_width: Original image width
            original_height: Original image height
            max_width: Maximum allowed width
            max_height: Maximum allowed height
            maintain_aspect: Whether to maintain aspect ratio
            
        Returns:
            Tuple[int, int]: New (width, height)
        """
        if not maintain_aspect:
            return max_width, max_height
        
        # Calculate scaling factors
        width_scale = max_width / original_width
        height_scale = max_height / original_height
        
        # Use the smaller scale to ensure image fits within bounds
        scale = min(width_scale, height_scale)
        
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        
        return new_width, new_height
    
    @staticmethod
    def generate_color_from_string(text: str) -> str:
        """
        Generate consistent color from string (for avatars, etc.).
        
        Args:
            text: Input text
            
        Returns:
            str: Hex color code
        """
        if not text:
            return "#4CAF50"  # Default plant green
        
        # Create hash of the text
        hash_object = hashlib.md5(text.encode())
        hash_hex = hash_object.hexdigest()
        
        # Take first 6 characters as color
        color = "#" + hash_hex[:6]
        
        return color
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """
        Truncate text to specified length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            suffix: Suffix to add when truncated
            
        Returns:
            str: Truncated text
        """
        if not text or len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
    
    @staticmethod
    def normalize_search_term(term: str) -> str:
        """
        Normalize search term for better matching.
        
        Args:
            term: Search term
            
        Returns:
            str: Normalized search term
        """
        if not term:
            return ""
        
        # Convert to lowercase
        normalized = term.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove special characters except spaces and hyphens
        normalized = re.sub(r'[^\w\s\-]', '', normalized)
        
        return normalized
    
    @staticmethod
    def calculate_similarity_score(text1: str, text2: str) -> float:
        """
        Calculate simple similarity score between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            float: Similarity score (0-1)
        """
        if not text1 or not text2:
            return 0.0
        
        # Normalize texts
        norm1 = PlantCareHelpers.normalize_search_term(text1)
        norm2 = PlantCareHelpers.normalize_search_term(text2)
        
        # Simple word-based similarity
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    @staticmethod
    def get_season_from_date(date_input: Union[datetime, date]) -> str:
        """
        Get season from date (Northern Hemisphere).
        
        Args:
            date_input: Date to check
            
        Returns:
            str: Season name
        """
        try:
            if isinstance(date_input, datetime):
                month = date_input.month
            else:
                month = date_input.month
            
            if month in [12, 1, 2]:
                return "winter"
            elif month in [3, 4, 5]:
                return "spring"
            elif month in [6, 7, 8]:
                return "summer"
            else:  # 9, 10, 11
                return "fall"
                
        except AttributeError:
            return "unknown"
    
    @staticmethod
    def round_decimal(value: Union[int, float, Decimal], places: int = 2) -> Decimal:
        """
        Round decimal to specified places.
        
        Args:
            value: Value to round
            places: Number of decimal places
            
        Returns:
            Decimal: Rounded value
        """
        if isinstance(value, Decimal):
            decimal_value = value
        else:
            decimal_value = Decimal(str(value))
        
        return decimal_value.quantize(
            Decimal('0.' + '0' * places),
            rounding=ROUND_HALF_UP
        )
    
    @staticmethod
    def safe_divide(numerator: Union[int, float], denominator: Union[int, float]) -> float:
        """
        Safely divide two numbers, returning 0 if denominator is 0.
        
        Args:
            numerator: Numerator
            denominator: Denominator
            
        Returns:
            float: Result of division or 0
        """
        try:
            return float(numerator) / float(denominator) if denominator != 0 else 0.0
        except (ValueError, TypeError, ZeroDivisionError):
            return 0.0
    
    @staticmethod
    def batch_process(items: List[Any], batch_size: int = 100) -> List[List[Any]]:
        """
        Split list into batches for processing.
        
        Args:
            items: List of items to batch
            batch_size: Size of each batch
            
        Returns:
            List[List[Any]]: List of batches
        """
        if not items:
            return []
        
        batches = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batches.append(batch)
        
        return batches
    
    @staticmethod
    def merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two dictionaries recursively.
        
        Args:
            dict1: First dictionary
            dict2: Second dictionary
            
        Returns:
            Dict: Merged dictionary
        """
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = PlantCareHelpers.merge_dicts(result[key], value)
            else:
                result[key] = value
        
        return result


# Convenience functions
def generate_plant_id() -> str:
    """Generate unique plant ID."""
    return PlantCareHelpers.generate_plant_id()


def clean_plant_name(name: str) -> str:
    """Clean plant name."""
    return PlantCareHelpers.clean_plant_name(name)


def calculate_next_watering(last_watered: Union[datetime, str], frequency: str) -> datetime:
    """Calculate next watering date."""
    return PlantCareHelpers.calculate_next_care_date(last_watered, frequency)


def generate_care_reminder(plant_name: str, care_type: str, days_overdue: int = 0) -> str:
    """Generate care reminder message."""
    return PlantCareHelpers.generate_care_reminder_message(plant_name, care_type, days_overdue)


def format_file_size(size_bytes: int) -> str:
    """Format file size."""
    return PlantCareHelpers.format_file_size(size_bytes)


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text."""
    return PlantCareHelpers.truncate_text(text, max_length)


def get_current_season() -> str:
    """Get current season."""
    return PlantCareHelpers.get_season_from_date(datetime.now())


def batch_items(items: List[Any], batch_size: int = 100) -> List[List[Any]]:
    """Batch items for processing."""
    return PlantCareHelpers.batch_process(items, batch_size)