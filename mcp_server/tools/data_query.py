"""
Data Query Tools

Implements P0 core data query tools.
"""

from typing import Dict, List, Optional

from ..services.data_service import DataService
from ..utils.validators import (
    validate_platforms,
    validate_limit,
    validate_keyword,
    validate_date_range,
    validate_top_n,
    validate_mode,
    validate_date_query
)
from ..utils.errors import MCPError


class DataQueryTools:
    """Data Query Tools Class"""

    def __init__(self, project_root: str = None):
        """
        Initialize data query tools

        Args:
            project_root: Project root directory
        """
        self.data_service = DataService(project_root)

    def get_latest_news(
        self,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = False
    ) -> Dict:
        """
        Get the latest batch of crawled news data.

        Args:
            platforms: List of platform IDs, e.g., ['zhihu', 'weibo']
            limit: Return limit, default 20
            include_url: Whether to include URLs, default False (saves tokens)

        Returns:
            Dictionary containing news list

        Example:
            >>> tools = DataQueryTools()
            >>> result = tools.get_latest_news(platforms=['zhihu'], limit=10)
            >>> print(result['total'])
            10
        """
        try:
            # Validate parameters
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # Get data
            news_list = self.data_service.get_latest_news(
                platforms=platforms,
                limit=limit,
                include_url=include_url
            )

            return {
                "news": news_list,
                "total": len(news_list),
                "platforms": platforms,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def search_news_by_keyword(
        self,
        keyword: str,
        date_range: Optional[Dict] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Search historical news by keyword.

        Args:
            keyword: Search keyword (required)
            date_range: Date range, format: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
            platforms: List of platforms to filter
            limit: Return limit (optional, returns all by default)

        Returns:
            Search result dictionary

        Example (Assuming today is 2025-11-17):
            >>> tools = DataQueryTools()
            >>> result = tools.search_news_by_keyword(
            ...     keyword="Artificial Intelligence",
            ...     date_range={"start": "2025-11-08", "end": "2025-11-17"},
            ...     limit=50
            ... )
            >>> print(result['total'])
        """
        try:
            # Validate parameters
            keyword = validate_keyword(keyword)
            date_range_tuple = validate_date_range(date_range)
            platforms = validate_platforms(platforms)

            if limit is not None:
                limit = validate_limit(limit, default=100)

            # Search data
            search_result = self.data_service.search_news_by_keyword(
                keyword=keyword,
                date_range=date_range_tuple,
                platforms=platforms,
                limit=limit
            )

            return {
                **search_result,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def get_trending_topics(
        self,
        top_n: Optional[int] = None,
        mode: Optional[str] = None
    ) -> Dict:
        """
        Get frequency statistics for personal watchlist keywords in news.

        Note: This tool calculates statistics based on the personal watchlist in
        config/frequency_words.txt, rather than automatically extracting hot topics
        from news. This is a customizable watchlist, and users can add or remove
        keywords according to their interests.

        Args:
            top_n: Return TOP N watchlist words, default 10
            mode: Mode - daily (daily cumulative), current (latest batch), incremental (incremental)

        Returns:
            Watchlist word frequency statistics dictionary, containing the count of each keyword in the news

        Example:
            >>> tools = DataQueryTools()
            >>> result = tools.get_trending_topics(top_n=5, mode="current")
            >>> print(len(result['topics']))
            5
            >>> # Returns frequency stats for keywords set in frequency_words.txt
        """
        try:
            # Validate parameters
            top_n = validate_top_n(top_n, default=10)
            valid_modes = ["daily", "current", "incremental"]
            mode = validate_mode(mode, valid_modes, default="current")

            # Get trending topics
            trending_result = self.data_service.get_trending_topics(
                top_n=top_n,
                mode=mode
            )

            return {
                **trending_result,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }

    def get_news_by_date(
        self,
        date_query: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = False
    ) -> Dict:
        """
        Query news by date, supports natural language date queries.

        Args:
            date_query: Date query string (optional, default "today"), supports:
                - Relative date: today, yesterday, day before yesterday, 3 days ago
                - Weekdays: last monday, this friday
                - Absolute date: 2025-10-10, Oct 10th
            platforms: List of platform IDs, e.g., ['zhihu', 'weibo']
            limit: Return limit, default 50
            include_url: Whether to include URLs, default False (saves tokens)

        Returns:
            Dictionary containing news list

        Example:
            >>> tools = DataQueryTools()
            >>> # Default to today if date not specified
            >>> result = tools.get_news_by_date(platforms=['zhihu'], limit=20)
            >>> # Specific date
            >>> result = tools.get_news_by_date(
            ...     date_query="yesterday",
            ...     platforms=['zhihu'],
            ...     limit=20
            ... )
            >>> print(result['total'])
            20
        """
        try:
            # Validate parameters - default today
            if date_query is None:
                date_query = "today"
            target_date = validate_date_query(date_query)
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # Get data
            news_list = self.data_service.get_news_by_date(
                target_date=target_date,
                platforms=platforms,
                limit=limit,
                include_url=include_url
            )

            return {
                "news": news_list,
                "total": len(news_list),
                "date": target_date.strftime("%Y-%m-%d"),
                "date_query": date_query,
                "platforms": platforms,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }