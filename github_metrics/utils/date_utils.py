# utils/date_utils.py
from datetime import datetime, timedelta
import pytz

def parse_date_string(date_str, logger):
    """
    Parse a date string into a datetime object with UTC timezone.
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format
        logger: Logger instance for error reporting
        
    Returns:
        datetime: Datetime object with UTC timezone or None if parsing fails
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        # Add UTC timezone
        return pytz.UTC.localize(date_obj)
    except ValueError as e:
        logger.error(f"Invalid date format: {str(e)}")
        return None

def get_date_range(start_str, end_str, logger):
    """
    Get a start and end date range from string inputs.
    
    Args:
        start_str (str): Start date string in YYYY-MM-DD format
        end_str (str): End date string in YYYY-MM-DD format
        logger: Logger instance for error reporting
        
    Returns:
        tuple: (start_date, end_date) with UTC timezone or None if parsing fails
    """
    start_date = parse_date_string(start_str, logger)
    end_date = parse_date_string(end_str, logger)
    
    if not start_date or not end_date:
        return None, None
    
    if start_date >= end_date:
        logger.error("Start date must be before end date")
        return None, None
    
    return start_date, end_date

def get_relative_date_range(days, logger):
    """
    Get a date range for the last N days.
    
    Args:
        days (int): Number of days to look back
        logger: Logger instance for error reporting
        
    Returns:
        tuple: (start_date, end_date) with UTC timezone
    """
    now = datetime.now(pytz.UTC)
    start_date = now - timedelta(days=days)
    return start_date, now

def format_date_for_display(date_obj):
    """
    Format a datetime object for display.
    
    Args:
        date_obj (datetime): Datetime object
        
    Returns:
        str: Formatted date string
    """
    if not date_obj:
        return ''
    
    return date_obj.strftime('%Y-%m-%d')