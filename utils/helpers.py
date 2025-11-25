"""
Utility helper functions
"""

import uuid
import hashlib
import asyncio
from functools import wraps
from typing import Callable, Any
from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger(__name__)


def generate_ticket_id() -> str:
    """
    Generate unique ticket ID
    
    Returns:
        Unique ticket ID (e.g., TKT-20231215-ABC123)
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    unique_id = uuid.uuid4().hex[:6].upper()
    return f"TKT-{timestamp}-{unique_id}"


def calculate_priority(sentiment: str, urgency: str, category: str) -> str:
    """
    Calculate ticket priority based on multiple factors
    
    Args:
        sentiment: Customer sentiment (positive, neutral, negative, very_negative)
        urgency: Issue urgency (low, medium, high, critical)
        category: Issue category
        
    Returns:
        Priority level (low, medium, high)
    """
    score = 0
    
    # Sentiment scoring
    sentiment_scores = {
        "very_negative": 3,
        "negative": 2,
        "neutral": 1,
        "positive": 0
    }
    score += sentiment_scores.get(sentiment, 1)
    
    # Urgency scoring
    urgency_scores = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1
    }
    score += urgency_scores.get(urgency, 2)
    
    # Category scoring (certain categories are always high priority)
    high_priority_categories = ["duplicate_payment", "account_access", "technical_issue"]
    if category in high_priority_categories:
        score += 2
    
    # Determine final priority
    if score >= 6:
        return "high"
    elif score >= 3:
        return "medium"
    else:
        return "low"


def hash_customer_id(customer_id: str) -> str:
    """
    Hash customer ID for privacy
    
    Args:
        customer_id: Original customer ID
        
    Returns:
        Hashed customer ID
    """
    return hashlib.sha256(customer_id.encode()).hexdigest()[:16]


def format_duration(seconds: int) -> str:
    """
    Format duration in human-readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours}h"
    else:
        days = seconds // 86400
        return f"{days}d"


def sanitize_message(message: str, max_length: int = 500) -> str:
    """
    Sanitize user message
    
    Args:
        message: Original message
        max_length: Maximum length
        
    Returns:
        Sanitized message
    """
    # Remove excessive whitespace
    message = ' '.join(message.split())
    
    # Truncate if too long
    if len(message) > max_length:
        message = message[:max_length] + "..."
    
    return message


def retry_async(max_retries: int = 3, delay: int = 5):
    """
    Decorator for retrying async functions
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"⚠️ Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {str(e)}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"❌ All {max_retries} attempts failed for {func.__name__}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def validate_channel(channel: str) -> bool:
    """
    Validate communication channel
    
    Args:
        channel: Channel name
        
    Returns:
        True if valid
    """
    valid_channels = ["email", "sms", "whatsapp"]
    return channel.lower() in valid_channels


def get_sla_deadline(priority: str) -> datetime:
    """
    Calculate SLA deadline based on priority
    
    Args:
        priority: Ticket priority
        
    Returns:
        SLA deadline datetime
    """
    from datetime import timedelta
    from config.settings import settings
    
    hours = settings.SLA_HOURS.get(priority, 24)
    return datetime.utcnow() + timedelta(hours=hours)


class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        logger.debug(f"⏱️ Starting: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.utcnow()
        duration = (self.end_time - self.start_time).total_seconds()
        
        if exc_type is None:
            logger.debug(f"✅ Completed: {self.operation_name} ({duration:.2f}s)")
        else:
            logger.error(f"❌ Failed: {self.operation_name} ({duration:.2f}s)")
        
        return False
