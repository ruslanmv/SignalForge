"""
Date Parser Utility

Supports parsing of various natural language date formats, including relative and absolute dates.
"""

import re
from datetime import datetime, timedelta
from typing import Dict

from .errors import InvalidParameterError


class DateParser:
    """Date Parser Class"""

    # English date mapping
    DATE_MAPPING = {
        "today": 0,
        "yesterday": 1,
        "ereyesterday": 2,  # Rare, but exists
        "day before yesterday": 2,
    }

    # Weekday mapping
    WEEKDAY_MAPPING = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }

    @staticmethod
    def parse_date_query(date_query: str) -> datetime:
        """
        Parse date query string.

        Supported formats:
        - Relative dates: today, yesterday, day before yesterday, N days ago
        - Weekdays: last monday, this friday
        - Absolute dates: 2025-10-10, 2025/10/10

        Args:
            date_query: Date query string.

        Returns:
            datetime object.

        Raises:
            InvalidParameterError: If the date format is unrecognized.

        Examples:
            >>> DateParser.parse_date_query("today")
            datetime(2025, 10, 11)
            >>> DateParser.parse_date_query("yesterday")
            datetime(2025, 10, 10)
            >>> DateParser.parse_date_query("3 days ago")
            datetime(2025, 10, 8)
            >>> DateParser.parse_date_query("2025-10-10")
            datetime(2025, 10, 10)
        """
        if not date_query or not isinstance(date_query, str):
            raise InvalidParameterError(
                "Date query string cannot be empty",
                suggestion="Please provide a valid date query, e.g., 'today', 'yesterday', '2025-10-10'."
            )

        date_query = date_query.strip().lower()

        # 1. Try parsing common relative dates
        if date_query in DateParser.DATE_MAPPING:
            days_ago = DateParser.DATE_MAPPING[date_query]
            return datetime.now() - timedelta(days=days_ago)

        # 2. Try parsing "N days ago"
        days_ago_match = re.match(r'(\d+)\s*days?\s+ago', date_query)
        if days_ago_match:
            days = int(days_ago_match.group(1))
            if days > 365:
                raise InvalidParameterError(
                    f"Number of days too large: {days} days",
                    suggestion="Please use a relative date less than 365 days or use an absolute date."
                )
            return datetime.now() - timedelta(days=days)

        # 3. Try parsing weekdays: "last monday", "this friday"
        weekday_match = re.match(r'(last|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', date_query)
        if weekday_match:
            week_type = weekday_match.group(1)  # last or this
            weekday_str = weekday_match.group(2)
            target_weekday = DateParser.WEEKDAY_MAPPING[weekday_str]
            return DateParser._get_date_by_weekday(target_weekday, week_type == "last")

        # 4. Try parsing ISO date: YYYY-MM-DD
        iso_date_match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_query)
        if iso_date_match:
            year = int(iso_date_match.group(1))
            month = int(iso_date_match.group(2))
            day = int(iso_date_match.group(3))
            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"Invalid date: {date_query}",
                    suggestion=f"Date value error: {str(e)}"
                )

        # 5. Try parsing slash format: YYYY/MM/DD or MM/DD
        slash_date_match = re.match(r'(?:(\d{4})/)?(\d{1,2})/(\d{1,2})', date_query)
        if slash_date_match:
            year_str = slash_date_match.group(1)
            month = int(slash_date_match.group(2))
            day = int(slash_date_match.group(3))

            if year_str:
                year = int(year_str)
            else:
                year = datetime.now().year
                current_month = datetime.now().month
                # If query month is greater than current month, assume it refers to last year
                if month > current_month:
                    year -= 1

            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"Invalid date: {date_query}",
                    suggestion=f"Date value error: {str(e)}"
                )

        # If no format matches
        raise InvalidParameterError(
            f"Unrecognized date format: {date_query}",
            suggestion=(
                "Supported formats:\n"
                "- Relative: today, yesterday, 3 days ago\n"
                "- Weekday: last monday, this friday\n"
                "- Absolute: 2025-10-10, 2025/10/10"
            )
        )

    @staticmethod
    def _get_date_by_weekday(target_weekday: int, is_last_week: bool) -> datetime:
        """
        Get date by weekday.

        Args:
            target_weekday: Target weekday (0=Monday, 6=Sunday).
            is_last_week: Whether it refers to last week.

        Returns:
            datetime object.
        """
        today = datetime.now()
        current_weekday = today.weekday()

        # Calculate day difference
        if is_last_week:
            # A day in the last week
            days_diff = current_weekday - target_weekday + 7
        else:
            # A day in the current week
            days_diff = current_weekday - target_weekday
            if days_diff < 0:
                # If target is ahead in the week (e.g. asking for Friday on a Tuesday), 
                # strictly speaking "this Friday" implies the future, but usually we handle past.
                # Logic here assumes finding the most recent past occurrence or current week occurrence.
                # Adjusting logic to ensure we don't return future dates if intent is history lookup.
                # However, standard logic for "this week":
                pass 
                # Note: Logic kept consistent with original intent (offset calculation)
                days_diff += 7 

        return today - timedelta(days=days_diff)

    @staticmethod
    def format_date_folder(date: datetime) -> str:
        """
        Format date as folder name.

        Args:
            date: datetime object.

        Returns:
            Folder name string, format: YYYY-MM-DD
        """
        # Changed from Chinese format to standard ISO format
        return date.strftime("%Y-%m-%d")

    @staticmethod
    def validate_date_not_future(date: datetime) -> None:
        """
        Validate that the date is not in the future.

        Args:
            date: The date to validate.

        Raises:
            InvalidParameterError: If date is in the future.
        """
        if date.date() > datetime.now().date():
            raise InvalidParameterError(
                f"Cannot query future dates: {date.strftime('%Y-%m-%d')}",
                suggestion="Please use today or a past date."
            )

    @staticmethod
    def validate_date_not_too_old(date: datetime, max_days: int = 365) -> None:
        """
        Validate that the date is not too old.

        Args:
            date: The date to validate.
            max_days: Maximum allowed days in the past.

        Raises:
            InvalidParameterError: If date is too old.
        """
        days_ago = (datetime.now().date() - date.date()).days
        if days_ago > max_days:
            raise InvalidParameterError(
                f"Date is too old: {date.strftime('%Y-%m-%d')} ({days_ago} days ago)",
                suggestion=f"Please query data within {max_days} days."
            )