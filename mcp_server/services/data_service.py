"""
Data Access Service

Provides a unified data query interface and encapsulates data access logic.
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .cache_service import get_cache
from .parser_service import ParserService
from ..utils.errors import DataNotFoundError


class DataService:
    """Data access service class"""

    def __init__(self, project_root: str = None):
        """
        Initialize the data service.

        Args:
            project_root: The root directory of the project.
        """
        self.parser = ParserService(project_root)
        self.cache = get_cache()

    def get_latest_news(
        self,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        include_url: bool = False
    ) -> List[Dict]:
        """
        Get the latest batch of crawled news data.

        Args:
            platforms: List of platform IDs. None means all platforms.
            limit: Limit the number of returned items.
            include_url: Whether to include URL links. Default is False (to save tokens).

        Returns:
            List of news items.

        Raises:
            DataNotFoundError: If data does not exist.
        """
        # Try to get from cache
        cache_key = f"latest_news:{','.join(platforms or [])}:{limit}:{include_url}"
        cached = self.cache.get(cache_key, ttl=900)  # 15 minutes cache
        if cached:
            return cached

        # Read today's data
        all_titles, id_to_name, timestamps = self.parser.read_all_titles_for_date(
            date=None,
            platform_ids=platforms
        )

        # Get the timestamp of the latest file
        if timestamps:
            latest_timestamp = max(timestamps.values())
            fetch_time = datetime.fromtimestamp(latest_timestamp)
        else:
            fetch_time = datetime.now()

        # Convert to news list
        news_list = []
        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # Take the first rank
                rank = info["ranks"][0] if info["ranks"] else 0

                news_item = {
                    "title": title,
                    "platform": platform_id,
                    "platform_name": platform_name,
                    "rank": rank,
                    "timestamp": fetch_time.strftime("%Y-%m-%d %H:%M:%S")
                }

                # Conditionally add URL fields
                if include_url:
                    news_item["url"] = info.get("url", "")
                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                news_list.append(news_item)

        # Sort by rank
        news_list.sort(key=lambda x: x["rank"])

        # Limit the returned quantity
        result = news_list[:limit]

        # Cache the result
        self.cache.set(cache_key, result)

        return result

    def get_news_by_date(
        self,
        target_date: datetime,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        include_url: bool = False
    ) -> List[Dict]:
        """
        Get news by a specific date.

        Args:
            target_date: The target date.
            platforms: List of platform IDs. None means all platforms.
            limit: Limit the number of returned items.
            include_url: Whether to include URL links. Default is False (to save tokens).

        Returns:
            List of news items.

        Raises:
            DataNotFoundError: If data does not exist.

        Examples:
            >>> service = DataService()
            >>> news = service.get_news_by_date(
            ...     target_date=datetime(2025, 10, 10),
            ...     platforms=['zhihu'],
            ...     limit=20
            ... )
        """
        # Try to get from cache
        date_str = target_date.strftime("%Y-%m-%d")
        cache_key = f"news_by_date:{date_str}:{','.join(platforms or [])}:{limit}:{include_url}"
        cached = self.cache.get(cache_key, ttl=1800)  # 30 minutes cache
        if cached:
            return cached

        # Read data for the specified date
        all_titles, id_to_name, timestamps = self.parser.read_all_titles_for_date(
            date=target_date,
            platform_ids=platforms
        )

        # Convert to news list
        news_list = []
        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # Calculate average rank
                avg_rank = sum(info["ranks"]) / len(info["ranks"]) if info["ranks"] else 0

                news_item = {
                    "title": title,
                    "platform": platform_id,
                    "platform_name": platform_name,
                    "rank": info["ranks"][0] if info["ranks"] else 0,
                    "avg_rank": round(avg_rank, 2),
                    "count": len(info["ranks"]),
                    "date": date_str
                }

                # Conditionally add URL fields
                if include_url:
                    news_item["url"] = info.get("url", "")
                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                news_list.append(news_item)

        # Sort by rank
        news_list.sort(key=lambda x: x["rank"])

        # Limit the returned quantity
        result = news_list[:limit]

        # Cache the result (historical data cached longer)
        self.cache.set(cache_key, result)

        return result

    def search_news_by_keyword(
        self,
        keyword: str,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Search for news by keyword.

        Args:
            keyword: Search keyword.
            date_range: Date range (start_date, end_date).
            platforms: List of platforms to filter by.
            limit: Limit the number of returned items (optional).

        Returns:
            Dictionary containing search results.

        Raises:
            DataNotFoundError: If data does not exist.
        """
        # Determine search date range
        if date_range:
            start_date, end_date = date_range
        else:
            # Default to searching today
            start_date = end_date = datetime.now()

        # Collect all matching news
        results = []
        platform_distribution = Counter()

        # Iterate through date range
        current_date = start_date
        while current_date <= end_date:
            try:
                all_titles, id_to_name, _ = self.parser.read_all_titles_for_date(
                    date=current_date,
                    platform_ids=platforms
                )

                # Search for titles containing the keyword
                for platform_id, titles in all_titles.items():
                    platform_name = id_to_name.get(platform_id, platform_id)

                    for title, info in titles.items():
                        if keyword.lower() in title.lower():
                            # Calculate average rank
                            avg_rank = sum(info["ranks"]) / len(info["ranks"]) if info["ranks"] else 0

                            results.append({
                                "title": title,
                                "platform": platform_id,
                                "platform_name": platform_name,
                                "ranks": info["ranks"],
                                "count": len(info["ranks"]),
                                "avg_rank": round(avg_rank, 2),
                                "url": info.get("url", ""),
                                "mobileUrl": info.get("mobileUrl", ""),
                                "date": current_date.strftime("%Y-%m-%d")
                            })

                            platform_distribution[platform_id] += 1

            except DataNotFoundError:
                # No data for this date, continue to next day
                pass

            # Next day
            current_date += timedelta(days=1)

        if not results:
            raise DataNotFoundError(
                f"No news found containing keyword '{keyword}'",
                suggestion="Please try other keywords or expand the date range."
            )

        # Calculate statistics
        total_ranks = []
        for item in results:
            total_ranks.extend(item["ranks"])

        avg_rank = sum(total_ranks) / len(total_ranks) if total_ranks else 0

        # Limit returned quantity (if specified)
        total_found = len(results)
        if limit is not None and limit > 0:
            results = results[:limit]

        return {
            "results": results,
            "total": len(results),
            "total_found": total_found,
            "statistics": {
                "platform_distribution": dict(platform_distribution),
                "avg_rank": round(avg_rank, 2),
                "keyword": keyword
            }
        }

    def get_trending_topics(
        self,
        top_n: int = 10,
        mode: str = "current"
    ) -> Dict:
        """
        Get frequency statistics for personal watchlist keywords in news.

        Note: This tool calculates statistics based on the personal watchlist in
        config/frequency_words.txt, rather than automatically extracting hot topics
        from news. Users can customize this watchlist.

        Args:
            top_n: Return TOP N watchlist words.
            mode: Mode - daily (daily cumulative), current (latest batch).

        Returns:
            Dictionary of watchlist word frequency statistics.

        Raises:
            DataNotFoundError: If data does not exist.
        """
        # Try to get from cache
        cache_key = f"trending_topics:{top_n}:{mode}"
        cached = self.cache.get(cache_key, ttl=1800)  # 30 minutes cache
        if cached:
            return cached

        # Read today's data
        all_titles, id_to_name, timestamps = self.parser.read_all_titles_for_date()

        if not all_titles:
            raise DataNotFoundError(
                "No news data found for today",
                suggestion="Please ensure the crawler has run and generated data."
            )

        # Load keyword configuration
        word_groups = self.parser.parse_frequency_words()

        # Select title data to process based on mode
        titles_to_process = {}

        if mode == "daily":
            # daily mode: process all cumulative data for the day
            titles_to_process = all_titles

        elif mode == "current":
            # current mode: only process the latest batch of data (file with latest timestamp)
            if timestamps:
                # Find the latest timestamp
                latest_timestamp = max(timestamps.values())

                # Re-read, only getting data for the latest time
                # Here we reverse lookup the platform corresponding to the latest file via timestamps
                latest_titles, _, _ = self.parser.read_all_titles_for_date()

                # Since read_all_titles_for_date returns merged data from all files,
                # we need to filter out the latest batch via timestamps.
                # Simplified implementation: Use all current data as the latest batch
                # (Precise implementation requires parser service to support filtering by time)
                titles_to_process = latest_titles
            else:
                titles_to_process = all_titles

        else:
            raise ValueError(
                f"Unsupported mode: {mode}. Supported modes: daily, current"
            )

        # Count word frequency
        word_frequency = Counter()
        keyword_to_news = {}

        # Iterate through titles to process
        for platform_id, titles in titles_to_process.items():
            for title in titles.keys():
                # Match against each keyword group
                for group in word_groups:
                    all_words = group.get("required", []) + group.get("normal", [])

                    for word in all_words:
                        if word and word in title:
                            word_frequency[word] += 1

                            if word not in keyword_to_news:
                                keyword_to_news[word] = []
                            keyword_to_news[word].append(title)

        # Get TOP N keywords
        top_keywords = word_frequency.most_common(top_n)

        # Build topic list
        topics = []
        for keyword, frequency in top_keywords:
            matched_news = keyword_to_news.get(keyword, [])

            topics.append({
                "keyword": keyword,
                "frequency": frequency,
                "matched_news": len(set(matched_news)),  # Count distinct news
                "trend": "stable",  # TODO: Historical data needed to calculate trend
                "weight_score": 0.0  # TODO: Implement weight calculation
            })

        # Build result
        result = {
            "topics": topics,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": mode,
            "total_keywords": len(word_frequency),
            "description": self._get_mode_description(mode)
        }

        # Cache result
        self.cache.set(cache_key, result)

        return result

    def _get_mode_description(self, mode: str) -> str:
        """Get mode description"""
        descriptions = {
            "daily": "Daily Cumulative Stats",
            "current": "Latest Batch Stats"
        }
        return descriptions.get(mode, "Unknown Mode")

    def get_current_config(self, section: str = "all") -> Dict:
        """
        Get current system configuration.

        Args:
            section: Configuration section - all/crawler/push/keywords/weights

        Returns:
            Configuration dictionary.

        Raises:
            FileParseError: Configuration file parsing error.
        """
        # Try to get from cache
        cache_key = f"config:{section}"
        cached = self.cache.get(cache_key, ttl=3600)  # 1 hour cache
        if cached:
            return cached

        # Parse config file
        config_data = self.parser.parse_yaml_config()
        word_groups = self.parser.parse_frequency_words()

        # Return corresponding config based on section
        if section == "all" or section == "crawler":
            crawler_config = {
                "enable_crawler": config_data.get("crawler", {}).get("enable_crawler", True),
                "use_proxy": config_data.get("crawler", {}).get("use_proxy", False),
                "request_interval": config_data.get("crawler", {}).get("request_interval", 1),
                "retry_times": 3,
                "platforms": [p["id"] for p in config_data.get("platforms", [])]
            }

        if section == "all" or section == "push":
            push_config = {
                "enable_notification": config_data.get("notification", {}).get("enable_notification", True),
                "enabled_channels": [],
                "message_batch_size": config_data.get("notification", {}).get("message_batch_size", 20),
                "push_window": config_data.get("notification", {}).get("push_window", {})
            }

            # Detect configured notification channels
            webhooks = config_data.get("notification", {}).get("webhooks", {})
            if webhooks.get("feishu_url"):
                push_config["enabled_channels"].append("feishu")
            if webhooks.get("dingtalk_url"):
                push_config["enabled_channels"].append("dingtalk")
            if webhooks.get("wework_url"):
                push_config["enabled_channels"].append("wework")

        if section == "all" or section == "keywords":
            keywords_config = {
                "word_groups": word_groups,
                "total_groups": len(word_groups)
            }

        if section == "all" or section == "weights":
            weights_config = {
                "rank_weight": config_data.get("weight", {}).get("rank_weight", 0.6),
                "frequency_weight": config_data.get("weight", {}).get("frequency_weight", 0.3),
                "hotness_weight": config_data.get("weight", {}).get("hotness_weight", 0.1)
            }

        # Assemble result
        if section == "all":
            result = {
                "crawler": crawler_config,
                "push": push_config,
                "keywords": keywords_config,
                "weights": weights_config
            }
        elif section == "crawler":
            result = crawler_config
        elif section == "push":
            result = push_config
        elif section == "keywords":
            result = keywords_config
        elif section == "weights":
            result = weights_config
        else:
            result = {}

        # Cache result
        self.cache.set(cache_key, result)

        return result

    def get_available_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Scan the output directory and return the actual available date range.

        Returns:
            Tuple of (earliest_date, latest_date). Returns (None, None) if no data exists.

        Examples:
            >>> service = DataService()
            >>> earliest, latest = service.get_available_date_range()
            >>> print(f"Available date range: {earliest} to {latest}")
        """
        output_dir = self.parser.project_root / "output"

        if not output_dir.exists():
            return (None, None)

        available_dates = []

        # Iterate through date folders
        for date_folder in output_dir.iterdir():
            if date_folder.is_dir() and not date_folder.name.startswith('.'):
                # Parse date (Format: YYYY年MM月DD日)
                try:
                    # Regex matches Chinese format: Year(年)Month(月)Day(日)
                    date_match = re.match(r'(\d{4})年(\d{2})月(\d{2})日', date_folder.name)
                    if date_match:
                        folder_date = datetime(
                            int(date_match.group(1)),
                            int(date_match.group(2)),
                            int(date_match.group(3))
                        )
                        available_dates.append(folder_date)
                except Exception:
                    pass

        if not available_dates:
            return (None, None)

        return (min(available_dates), max(available_dates))

    def get_system_status(self) -> Dict:
        """
        Get system running status.

        Returns:
            System status dictionary.
        """
        # Get data statistics
        output_dir = self.parser.project_root / "output"

        total_storage = 0
        oldest_record = None
        latest_record = None

        if output_dir.exists():
            # Iterate through date folders
            for date_folder in output_dir.iterdir():
                if date_folder.is_dir():
                    # Parse date
                    try:
                        date_str = date_folder.name
                        # Format: YYYY年MM月DD日
                        date_match = re.match(r'(\d{4})年(\d{2})月(\d{2})日', date_str)
                        if date_match:
                            folder_date = datetime(
                                int(date_match.group(1)),
                                int(date_match.group(2)),
                                int(date_match.group(3))
                            )

                            if oldest_record is None or folder_date < oldest_record:
                                oldest_record = folder_date
                            if latest_record is None or folder_date > latest_record:
                                latest_record = folder_date

                    except:
                        pass

                    # Calculate storage size
                    for item in date_folder.rglob("*"):
                        if item.is_file():
                            total_storage += item.stat().st_size

        # Read version information
        version_file = self.parser.project_root / "version"
        version = "unknown"
        if version_file.exists():
            try:
                with open(version_file, "r") as f:
                    version = f.read().strip()
            except:
                pass

        return {
            "system": {
                "version": version,
                "project_root": str(self.parser.project_root)
            },
            "data": {
                "total_storage": f"{total_storage / 1024 / 1024:.2f} MB",
                "oldest_record": oldest_record.strftime("%Y-%m-%d") if oldest_record else None,
                "latest_record": latest_record.strftime("%Y-%m-%d") if latest_record else None,
            },
            "cache": self.cache.get_stats(),
            "health": "healthy"
        }