"""
Parameter Validation Tools

Provides unified parameter validation functionality.
"""

from datetime import datetime
from typing import List, Optional
import os
import yaml

from .errors import InvalidParameterError
from .date_parser import DateParser


def get_supported_platforms() -> List[str]:
    """
    Dynamically retrieve the list of supported platforms from config.yaml.

    Returns:
        List of platform IDs.

    Note:
        - Returns an empty list on failure, allowing all platforms (fallback strategy).
        - The platform list originates from the 'platforms' configuration in config/config.yaml.
    """
    try:
        # Get config.yaml path (relative to current file)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "..", "..", "config", "config.yaml")
        config_path = os.path.normpath(config_path)

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            platforms = config.get('platforms', [])
            return [p['id'] for p in platforms if 'id' in p]
    except Exception as e:
        # Fallback: Return empty list, allowing all platforms
        print(f"Warning: Failed to load platform config ({config_path}): {e}")
        return []


def validate_platforms(platforms: Optional[List[str]]) -> List[str]:
    """
    Validate the platform list.

    Args:
        platforms: List of platform IDs. None indicates using all platforms from config.yaml.

    Returns:
        Validated list of platform IDs.

    Raises:
        InvalidParameterError: If a platform is not supported.

    Note:
        - When platforms=None, returns the list from config.yaml.
        - Validates if platform IDs exist in config.yaml.
        - If config load fails, validation is skipped (fallback strategy).
    """
    supported_platforms = get_supported_platforms()

    if platforms is None:
        # Return platforms from config (user default)
        return supported_platforms if supported_platforms else []

    if not isinstance(platforms, list):
        raise InvalidParameterError("The 'platforms' parameter must be a list.")

    if not platforms:
        # If empty list, return platforms from config
        return supported_platforms if supported_platforms else []

    # If config failed to load (supported_platforms is empty), allow all
    if not supported_platforms:
        print("Warning: Platform config not loaded, skipping validation.")
        return platforms

    # Validate each platform
    invalid_platforms = [p for p in platforms if p not in supported_platforms]
    if invalid_platforms:
        raise InvalidParameterError(
            f"Unsupported platforms: {', '.join(invalid_platforms)}",
            suggestion=f"Supported platforms (from config.yaml): {', '.join(supported_platforms)}"
        )

    return platforms


def validate_limit(limit: Optional[int], default: int = 20, max_limit: int = 1000) -> int:
    """
    Validate limit parameter.

    Args:
        limit: The limit value.
        default: Default value.
        max_limit: Maximum allowed limit.

    Returns:
        Validated limit value.

    Raises:
        InvalidParameterError: If parameter is invalid.
    """
    if limit is None:
        return default

    if not isinstance(limit, int):
        raise InvalidParameterError("The 'limit' parameter must be an integer.")

    if limit <= 0:
        raise InvalidParameterError("Limit must be greater than 0.")

    if limit > max_limit:
        raise InvalidParameterError(
            f"Limit cannot exceed {max_limit}",
            suggestion="Please use pagination or reduce the limit value."
        )

    return limit


def validate_date(date_str: str) -> datetime:
    """
    Validate date format.

    Args:
        date_str: Date string (YYYY-MM-DD).

    Returns:
        datetime object.

    Raises:
        InvalidParameterError: If date format is incorrect.
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise InvalidParameterError(
            f"Invalid date format: {date_str}",
            suggestion="Please use YYYY-MM-DD format, e.g., 2025-10-11."
        )


def validate_date_range(date_range: Optional[dict]) -> Optional[tuple]:
    """
    Validate date range.

    Args:
        date_range: Dictionary {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}.

    Returns:
        Tuple (start_date, end_date), or None.

    Raises:
        InvalidParameterError: If date range is invalid.
    """
    if date_range is None:
        return None

    if not isinstance(date_range, dict):
        raise InvalidParameterError("date_range must be a dictionary.")

    start_str = date_range.get("start")
    end_str = date_range.get("end")

    if not start_str or not end_str:
        raise InvalidParameterError(
            "date_range must contain 'start' and 'end' fields",
            suggestion='Example: {"start": "2025-10-01", "end": "2025-10-11"}'
        )

    start_date = validate_date(start_str)
    end_date = validate_date(end_str)

    if start_date > end_date:
        raise InvalidParameterError(
            "Start date cannot be later than end date",
            suggestion=f"start: {start_str}, end: {end_str}"
        )

    # Check if dates are in the future
    today = datetime.now().date()
    if start_date.date() > today or end_date.date() > today:
        # Get available data range hint
        try:
            from ..services.data_service import DataService
            data_service = DataService()
            earliest, latest = data_service.get_available_date_range()

            if earliest and latest:
                available_range = f"{earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}"
            else:
                available_range = "No data available"
        except Exception:
            available_range = "Unknown (please check output directory)"

        future_dates = []
        if start_date.date() > today:
            future_dates.append(start_str)
        if end_date.date() > today and end_str != start_str:
            future_dates.append(end_str)

        raise InvalidParameterError(
            f"Querying future dates is not allowed: {', '.join(future_dates)} (Current date: {today.strftime('%Y-%m-%d')})",
            suggestion=f"Currently available data range: {available_range}"
        )

    return (start_date, end_date)


def validate_keyword(keyword: str) -> str:
    """
    Validate keyword.

    Args:
        keyword: Search keyword.

    Returns:
        Processed keyword.

    Raises:
        InvalidParameterError: If keyword is invalid.
    """
    if not keyword:
        raise InvalidParameterError("Keyword cannot be empty.")

    if not isinstance(keyword, str):
        raise InvalidParameterError("Keyword must be a string.")

    keyword = keyword.strip()

    if not keyword:
        raise InvalidParameterError("Keyword cannot consist only of whitespace.")

    if len(keyword) > 100:
        raise InvalidParameterError(
            "Keyword length cannot exceed 100 characters",
            suggestion="Please use a more concise keyword."
        )

    return keyword


def validate_top_n(top_n: Optional[int], default: int = 10) -> int:
    """
    Validate TOP N parameter.

    Args:
        top_n: TOP N count.
        default: Default value.

    Returns:
        Validated value.

    Raises:
        InvalidParameterError: If parameter is invalid.
    """
    return validate_limit(top_n, default=default, max_limit=100)


def validate_mode(mode: Optional[str], valid_modes: List[str], default: str) -> str:
    """
    Validate mode parameter.

    Args:
        mode: Mode string.
        valid_modes: List of valid modes.
        default: Default mode.

    Returns:
        Validated mode.

    Raises:
        InvalidParameterError: If mode is invalid.
    """
    if mode is None:
        return default

    if not isinstance(mode, str):
        raise InvalidParameterError("Mode must be a string.")

    if mode not in valid_modes:
        raise InvalidParameterError(
            f"Invalid mode: {mode}",
            suggestion=f"Supported modes: {', '.join(valid_modes)}"
        )

    return mode


def validate_config_section(section: Optional[str]) -> str:
    """
    Validate configuration section parameter.

    Args:
        section: Section name.

    Returns:
        Validated section.

    Raises:
        InvalidParameterError: If section is invalid.
    """
    valid_sections = ["all", "crawler", "push", "keywords", "weights"]
    return validate_mode(section, valid_sections, "all")


def validate_date_query(
    date_query: str,
    allow_future: bool = False,
    max_days_ago: int = 365
) -> datetime:
    """
    Validate and parse date query string.

    Args:
        date_query: Date query string.
        allow_future: Whether to allow future dates.
        max_days_ago: Maximum allowed days in the past.

    Returns:
        Parsed datetime object.

    Raises:
        InvalidParameterError: If date query is invalid.

    Examples:
        >>> validate_date_query("yesterday")
        datetime(2025, 10, 10)
        >>> validate_date_query("2025-10-10")
        datetime(2025, 10, 10)
    """
    if not date_query:
        raise InvalidParameterError(
            "Date query string cannot be empty",
            suggestion="Please provide a date query, e.g., 'today', 'yesterday', '2025-10-10'."
        )

    # Use DateParser to parse date
    parsed_date = DateParser.parse_date_query(date_query)

    # Validate date is not in the future
    if not allow_future:
        DateParser.validate_date_not_future(parsed_date)

    # Validate date is not too old
    DateParser.validate_date_not_too_old(parsed_date, max_days=max_days_ago)

    return parsed_date