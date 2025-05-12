# Add to new file: app/utils/datetime_utils.py

from datetime import datetime
import pytz
from typing import Optional, Dict, List

# Common timezones for selection
COMMON_TIMEZONES = [
    {"code": "UTC", "name": "UTC (Coordinated Universal Time)"},
    {"code": "America/New_York", "name": "Eastern Time (US & Canada)"},
    {"code": "America/Chicago", "name": "Central Time (US & Canada)"},
    {"code": "America/Denver", "name": "Mountain Time (US & Canada)"},
    {"code": "America/Los_Angeles", "name": "Pacific Time (US & Canada)"},
    {"code": "Europe/London", "name": "London"},
    {"code": "Europe/Paris", "name": "Paris, Berlin, Rome"},
    {"code": "Asia/Tokyo", "name": "Tokyo"},
    {"code": "Asia/Shanghai", "name": "Beijing, Shanghai"},
    {"code": "Australia/Sydney", "name": "Sydney"},
]

def get_current_time(timezone_str: str = "UTC") -> datetime:
    """
    Get current time in the specified timezone
    """
    try:
        timezone = pytz.timezone(timezone_str)
        return datetime.now(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        # Fallback to UTC
        return datetime.now(pytz.UTC)

def convert_timezone(dt: datetime, to_timezone: str) -> datetime:
    """
    Convert datetime to specified timezone
    """
    if dt.tzinfo is None:
        # Assume UTC if no timezone is provided
        dt = dt.replace(tzinfo=pytz.UTC)
    
    try:
        target_tz = pytz.timezone(to_timezone)
        return dt.astimezone(target_tz)
    except pytz.exceptions.UnknownTimeZoneError:
        # Return original if timezone is invalid
        return dt

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S", 
                   target_timezone: Optional[str] = None) -> str:
    """
    Format datetime to string in specified timezone
    """
    if target_timezone:
        dt = convert_timezone(dt, target_timezone)
    
    return dt.strftime(format_str)

def get_available_timezones() -> List[Dict[str, str]]:
    """
    Returns a list of common timezones for UI selection
    """
    return COMMON_TIMEZONES

def is_valid_timezone(tz_str: str) -> bool:
    """
    Check if timezone string is valid
    """
    try:
        pytz.timezone(tz_str)
        return True
    except pytz.exceptions.UnknownTimeZoneError:
        return False