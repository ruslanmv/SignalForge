"""
Advanced Analytics Tools

Provides advanced analysis functions such as popularity trend analysis, 
platform comparison, keyword co-occurrence, and sentiment analysis.
"""

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from difflib import SequenceMatcher

from ..services.data_service import DataService
from ..utils.validators import (
    validate_platforms,
    validate_limit,
    validate_keyword,
    validate_top_n,
    validate_date_range
)
from ..utils.errors import MCPError, InvalidParameterError, DataNotFoundError


def calculate_news_weight(news_data: Dict, rank_threshold: int = 5) -> float:
    """
    Calculate news weight (for sorting).

    Based on the weight algorithm in main.py, considering:
    - Rank Weight (60%): The rank of the news in the list.
    - Frequency Weight (30%): The number of times the news appears.
    - Hotness Weight (10%): The ratio of high-ranking appearances.

    Args:
        news_data: News data dictionary containing 'ranks' and 'count' fields.
        rank_threshold: Threshold for high ranking, default is 5.

    Returns:
        Weight score (float between 0-100).
    """
    ranks = news_data.get("ranks", [])
    if not ranks:
        return 0.0

    count = news_data.get("count", len(ranks))

    # Weight configuration (consistent with config.yaml)
    RANK_WEIGHT = 0.6
    FREQUENCY_WEIGHT = 0.3
    HOTNESS_WEIGHT = 0.1

    # 1. Rank Weight: Σ(11 - min(rank, 10)) / appearance_count
    rank_scores = []
    for rank in ranks:
        score = 11 - min(rank, 10)
        rank_scores.append(score)

    rank_weight = sum(rank_scores) / len(ranks) if ranks else 0

    # 2. Frequency Weight: min(count, 10) * 10
    frequency_weight = min(count, 10) * 10

    # 3. Hotness Bonus: high_rank_count / total_count * 100
    high_rank_count = sum(1 for rank in ranks if rank <= rank_threshold)
    hotness_ratio = high_rank_count / len(ranks) if ranks else 0
    hotness_weight = hotness_ratio * 100

    # Total Weight
    total_weight = (
        rank_weight * RANK_WEIGHT
        + frequency_weight * FREQUENCY_WEIGHT
        + hotness_weight * HOTNESS_WEIGHT
    )

    return total_weight


class AnalyticsTools:
    """Advanced Data Analytics Tools Class"""

    def __init__(self, project_root: str = None):
        """
        Initialize analytics tools.

        Args:
            project_root: Project root directory.
        """
        self.data_service = DataService(project_root)

    def analyze_data_insights_unified(
        self,
        insight_type: str = "platform_compare",
        topic: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None,
        min_frequency: int = 3,
        top_n: int = 20
    ) -> Dict:
        """
        Unified Data Insight Analysis Tool - Integrates multiple analysis modes.

        Args:
            insight_type: Type of insight, options:
                - "platform_compare": Platform comparison (compare attention on a topic across platforms).
                - "platform_activity": Platform activity stats (frequency and active times).
                - "keyword_cooccur": Keyword co-occurrence analysis (patterns of words appearing together).
            topic: Topic keyword (optional, applicable for platform_compare).
            date_range: Date range, format: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}.
            min_frequency: Minimum co-occurrence frequency (for keyword_cooccur), default 3.
            top_n: Return TOP N results (for keyword_cooccur), default 20.

        Returns:
            Dictionary containing data insight analysis results.

        Examples:
            - analyze_data_insights_unified(insight_type="platform_compare", topic="Artificial Intelligence")
            - analyze_data_insights_unified(insight_type="platform_activity", date_range={...})
            - analyze_data_insights_unified(insight_type="keyword_cooccur", min_frequency=5)
        """
        try:
            # Validate parameters
            if insight_type not in ["platform_compare", "platform_activity", "keyword_cooccur"]:
                raise InvalidParameterError(
                    f"Invalid insight type: {insight_type}",
                    suggestion="Supported types: platform_compare, platform_activity, keyword_cooccur"
                )

            # Call method based on insight type
            if insight_type == "platform_compare":
                return self.compare_platforms(
                    topic=topic,
                    date_range=date_range
                )
            elif insight_type == "platform_activity":
                return self.get_platform_activity_stats(
                    date_range=date_range
                )
            else:  # keyword_cooccur
                return self.analyze_keyword_cooccurrence(
                    min_frequency=min_frequency,
                    top_n=top_n
                )

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

    def analyze_topic_trend_unified(
        self,
        topic: str,
        analysis_type: str = "trend",
        date_range: Optional[Dict[str, str]] = None,
        granularity: str = "day",
        threshold: float = 3.0,
        time_window: int = 24,
        lookahead_hours: int = 6,
        confidence_threshold: float = 0.7
    ) -> Dict:
        """
        Unified Topic Trend Analysis Tool - Integrates multiple trend analysis modes.

        Args:
            topic: Topic keyword (required).
            analysis_type: Analysis type, options:
                - "trend": Popularity trend (track changes in topic popularity).
                - "lifecycle": Lifecycle analysis (full cycle from emergence to disappearance).
                - "viral": Viral anomaly detection (identify suddenly exploding topics).
                - "predict": Topic prediction (forecast future potential hotspots).
            date_range: Date range (for trend and lifecycle), optional.
                        - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                        - **Default**: Last 7 days if not specified.
            granularity: Time granularity (for trend), default "day" (hour/day).
            threshold: Sudden increase multiplier threshold (for viral), default 3.0.
            time_window: Detection time window in hours (for viral), default 24.
            lookahead_hours: Hours to predict into the future (for predict), default 6.
            confidence_threshold: Confidence threshold (for predict), default 0.7.

        Returns:
            Dictionary containing trend analysis results.

        Examples (Assuming today is 2025-11-17):
            - User: "Analyze AI trend for last 7 days" -> analyze_topic_trend_unified(topic="AI", analysis_type="trend", date_range={"start": "2025-11-11", "end": "2025-11-17"})
            - User: "Check Tesla's popularity this month" -> analyze_topic_trend_unified(topic="Tesla", analysis_type="lifecycle", date_range={"start": "2025-11-01", "end": "2025-11-17"})
            - analyze_topic_trend_unified(topic="Bitcoin", analysis_type="viral", threshold=3.0)
            - analyze_topic_trend_unified(topic="ChatGPT", analysis_type="predict", lookahead_hours=6)
        """
        try:
            # Validate parameters
            topic = validate_keyword(topic)

            if analysis_type not in ["trend", "lifecycle", "viral", "predict"]:
                raise InvalidParameterError(
                    f"Invalid analysis type: {analysis_type}",
                    suggestion="Supported types: trend, lifecycle, viral, predict"
                )

            # Call method based on analysis type
            if analysis_type == "trend":
                return self.get_topic_trend_analysis(
                    topic=topic,
                    date_range=date_range,
                    granularity=granularity
                )
            elif analysis_type == "lifecycle":
                return self.analyze_topic_lifecycle(
                    topic=topic,
                    date_range=date_range
                )
            elif analysis_type == "viral":
                # viral mode doesn't strictly need a topic argument for general detection
                return self.detect_viral_topics(
                    threshold=threshold,
                    time_window=time_window
                )
            else:  # predict
                # predict mode uses general historical data
                return self.predict_trending_topics(
                    lookahead_hours=lookahead_hours,
                    confidence_threshold=confidence_threshold
                )

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

    def get_topic_trend_analysis(
        self,
        topic: str,
        date_range: Optional[Dict[str, str]] = None,
        granularity: str = "day"
    ) -> Dict:
        """
        Trend Analysis - Track popularity changes of a specific topic.

        Args:
            topic: Topic keyword.
            date_range: Date range (optional).
                        - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                        - **Default**: Last 7 days if not specified.
            granularity: Time granularity, only 'day' is supported.

        Returns:
            Trend analysis result dictionary.

        Examples:
            User queries:
            - "Analyze the trend of 'AI' for the last week"
            - "View popularity changes for 'Bitcoin' over the past week"
            - "See 'iPhone' trend for the last 7 days"

            Code call:
            >>> tools = AnalyticsTools()
            >>> result = tools.get_topic_trend_analysis(
            ...     topic="AI",
            ...     date_range={"start": "2025-11-11", "end": "2025-11-17"},
            ...     granularity="day"
            ... )
            >>> print(result['trend_data'])
        """
        try:
            # Validate parameters
            topic = validate_keyword(topic)

            # Validate granularity (only day supported)
            if granularity != "day":
                from ..utils.errors import InvalidParameterError
                raise InvalidParameterError(
                    f"Unsupported granularity: {granularity}",
                    suggestion="Currently only 'day' granularity is supported as data is aggregated daily."
                )

            # Handle date range (default to last 7 days)
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # Default last 7 days
                end_date = datetime.now()
                start_date = end_date - timedelta(days=6)

            # Collect trend data
            trend_data = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    # Count topic occurrences for this date
                    count = 0
                    matched_titles = []

                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            if topic.lower() in title.lower():
                                count += 1
                                matched_titles.append(title)

                    trend_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": count,
                        "sample_titles": matched_titles[:3]  # Keep only top 3 samples
                    })

                except DataNotFoundError:
                    trend_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": 0,
                        "sample_titles": []
                    })

                # Increment day
                current_date += timedelta(days=1)

            # Calculate trend indicators
            counts = [item["count"] for item in trend_data]
            total_days = (end_date - start_date).days + 1

            if len(counts) >= 2:
                # Calculate percentage change
                first_non_zero = next((c for c in counts if c > 0), 0)
                last_count = counts[-1]

                if first_non_zero > 0:
                    change_rate = ((last_count - first_non_zero) / first_non_zero) * 100
                else:
                    change_rate = 0

                # Find peak time
                max_count = max(counts)
                peak_index = counts.index(max_count)
                peak_time = trend_data[peak_index]["date"]
            else:
                change_rate = 0
                peak_time = None
                max_count = 0

            # Determine trend direction string
            direction = "Rising" if change_rate > 10 else "Falling" if change_rate < -10 else "Stable"

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                    "total_days": total_days
                },
                "granularity": granularity,
                "trend_data": trend_data,
                "statistics": {
                    "total_mentions": sum(counts),
                    "average_mentions": round(sum(counts) / len(counts), 2) if counts else 0,
                    "peak_count": max_count,
                    "peak_time": peak_time,
                    "change_rate": round(change_rate, 2)
                },
                "trend_direction": direction
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

    def compare_platforms(
        self,
        topic: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Platform Comparison - Compare attention for a topic across different platforms.

        Args:
            topic: Topic keyword (optional, compares overall activity if not specified).
            date_range: Date range, format: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}.

        Returns:
            Platform comparison result.

        Examples:
            User queries:
            - "Compare attention on 'AI' across platforms"
            - "Which platform cares more about tech news, Zhihu or Weibo?"
            - "Analyze today's hotspot distribution by platform"
        """
        try:
            # Validate parameters
            if topic:
                topic = validate_keyword(topic)
            date_range_tuple = validate_date_range(date_range)

            # Determine date range
            if date_range_tuple:
                start_date, end_date = date_range_tuple
            else:
                start_date = end_date = datetime.now()

            # Collect data per platform
            platform_stats = defaultdict(lambda: {
                "total_news": 0,
                "topic_mentions": 0,
                "unique_titles": set(),
                "top_keywords": Counter()
            })

            # Iterate through date range
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        for title in titles.keys():
                            platform_stats[platform_name]["total_news"] += 1
                            platform_stats[platform_name]["unique_titles"].add(title)

                            # Count topic mentions if topic is specified
                            if topic and topic.lower() in title.lower():
                                platform_stats[platform_name]["topic_mentions"] += 1

                            # Extract keywords
                            keywords = self._extract_keywords(title)
                            platform_stats[platform_name]["top_keywords"].update(keywords)

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # Convert to serializable format
            result_stats = {}
            for platform, stats in platform_stats.items():
                coverage_rate = 0
                if stats["total_news"] > 0:
                    coverage_rate = (stats["topic_mentions"] / stats["total_news"]) * 100

                result_stats[platform] = {
                    "total_news": stats["total_news"],
                    "topic_mentions": stats["topic_mentions"],
                    "unique_titles": len(stats["unique_titles"]),
                    "coverage_rate": round(coverage_rate, 2),
                    "top_keywords": [
                        {"keyword": k, "count": v}
                        for k, v in stats["top_keywords"].most_common(5)
                    ]
                }

            # Find unique topics per platform
            unique_topics = self._find_unique_topics(platform_stats)

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "platform_stats": result_stats,
                "unique_topics": unique_topics,
                "total_platforms": len(result_stats)
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

    def analyze_keyword_cooccurrence(
        self,
        min_frequency: int = 3,
        top_n: int = 20
    ) -> Dict:
        """
        Keyword Co-occurrence Analysis - Analyze which keywords frequently appear together.

        Args:
            min_frequency: Minimum co-occurrence frequency.
            top_n: Return TOP N keyword pairs.

        Returns:
            Keyword co-occurrence analysis results.
        """
        try:
            # Validate parameters
            min_frequency = validate_limit(min_frequency, default=3, max_limit=100)
            top_n = validate_top_n(top_n, default=20)

            # Read today's data
            all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

            # Keyword co-occurrence stats
            cooccurrence = Counter()
            keyword_titles = defaultdict(list)

            for platform_id, titles in all_titles.items():
                for title in titles.keys():
                    # Extract keywords
                    keywords = self._extract_keywords(title)

                    # Record titles for each keyword
                    for kw in keywords:
                        keyword_titles[kw].append(title)

                    # Calculate pairwise co-occurrence
                    if len(keywords) >= 2:
                        for i, kw1 in enumerate(keywords):
                            for kw2 in keywords[i+1:]:
                                # Sort to avoid duplicates
                                pair = tuple(sorted([kw1, kw2]))
                                cooccurrence[pair] += 1

            # Filter low frequency pairs
            filtered_pairs = [
                (pair, count) for pair, count in cooccurrence.items()
                if count >= min_frequency
            ]

            # Sort and take TOP N
            top_pairs = sorted(filtered_pairs, key=lambda x: x[1], reverse=True)[:top_n]

            # Build result
            result_pairs = []
            for (kw1, kw2), count in top_pairs:
                # Find sample titles containing both keywords
                titles_with_both = [
                    title for title in keyword_titles[kw1]
                    if kw2 in self._extract_keywords(title)
                ]

                result_pairs.append({
                    "keyword1": kw1,
                    "keyword2": kw2,
                    "cooccurrence_count": count,
                    "sample_titles": titles_with_both[:3]
                })

            return {
                "success": True,
                "cooccurrence_pairs": result_pairs,
                "total_pairs": len(result_pairs),
                "min_frequency": min_frequency,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

    def analyze_sentiment(
        self,
        topic: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
        limit: int = 50,
        sort_by_weight: bool = True,
        include_url: bool = False
    ) -> Dict:
        """
        Sentiment Analysis - Generates structured prompts for AI sentiment analysis.

        This tool collects news data and generates optimized AI prompts that you can send to an AI for deep sentiment analysis.

        Args:
            topic: Topic keyword (optional), only analyzes news containing this keyword.
            platforms: List of platforms to filter (optional), e.g., ['zhihu', 'weibo'].
            date_range: Date range (optional), format: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}.
                        Defaults to today if not specified.
            limit: Limit the number of news items returned, default 50, max 100.
            sort_by_weight: Whether to sort by weight, default True (recommended).
            include_url: Whether to include URL links, default False (saves tokens).

        Returns:
            Structured result containing the AI prompt and news data.

        Examples:
            - "Analyze the sentiment of today's news"
            - "Is the news about 'Tesla' positive or negative?"
            - "Analyze the emotional attitude of various platforms towards 'AI'"
        """
        try:
            # Validate parameters
            if topic:
                topic = validate_keyword(topic)
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # Handle date range
            if date_range:
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # Default to today
                start_date = end_date = datetime.now()

            # Collect news data (supports multiple days)
            all_news_items = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date,
                        platform_ids=platforms
                    )

                    # Collect news for this date
                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)
                        for title, info in titles.items():
                            # Filter by topic if specified
                            if topic and topic.lower() not in title.lower():
                                continue

                            news_item = {
                                "platform": platform_name,
                                "title": title,
                                "ranks": info.get("ranks", []),
                                "count": len(info.get("ranks", [])),
                                "date": current_date.strftime("%Y-%m-%d")
                            }

                            # Conditionally add URL fields
                            if include_url:
                                news_item["url"] = info.get("url", "")
                                news_item["mobileUrl"] = info.get("mobileUrl", "")

                            all_news_items.append(news_item)

                except DataNotFoundError:
                    # No data for this date, continue
                    pass

                # Next day
                current_date += timedelta(days=1)

            if not all_news_items:
                time_desc = "today" if start_date == end_date else f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                raise DataNotFoundError(
                    f"No relevant news found ({time_desc})",
                    suggestion="Please try other topics, date ranges, or platforms."
                )

            # Deduplicate (keep only one instance of same title per platform)
            unique_news = {}
            for item in all_news_items:
                key = f"{item['platform']}::{item['title']}"
                if key not in unique_news:
                    unique_news[key] = item
                else:
                    # Merge ranks (if news appeared on multiple days)
                    existing = unique_news[key]
                    existing["ranks"].extend(item["ranks"])
                    existing["count"] = len(existing["ranks"])

            deduplicated_news = list(unique_news.values())

            # Sort by weight (if enabled)
            if sort_by_weight:
                deduplicated_news.sort(
                    key=lambda x: calculate_news_weight(x),
                    reverse=True
                )

            # Limit returned quantity
            selected_news = deduplicated_news[:limit]

            # Generate AI Prompt
            ai_prompt = self._create_sentiment_analysis_prompt(
                news_data=selected_news,
                topic=topic
            )

            # Build time range description
            if start_date == end_date:
                time_range_desc = start_date.strftime("%Y-%m-%d")
            else:
                time_range_desc = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

            result = {
                "success": True,
                "method": "ai_prompt_generation",
                "summary": {
                    "total_found": len(deduplicated_news),
                    "returned_count": len(selected_news),
                    "requested_limit": limit,
                    "duplicates_removed": len(all_news_items) - len(deduplicated_news),
                    "topic": topic,
                    "time_range": time_range_desc,
                    "platforms": list(set(item["platform"] for item in selected_news)),
                    "sorted_by_weight": sort_by_weight
                },
                "ai_prompt": ai_prompt,
                "news_sample": selected_news,
                "usage_note": "Please send the content of the 'ai_prompt' field to the AI for sentiment analysis."
            }

            # Add note if fewer items returned than requested
            if len(selected_news) < limit and len(deduplicated_news) >= limit:
                result["note"] = "Returned count is less than requested limit due to deduplication."
            elif len(deduplicated_news) < limit:
                result["note"] = f"Only found {len(deduplicated_news)} matching news items in the specified date range."

            return result

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

    def _create_sentiment_analysis_prompt(
        self,
        news_data: List[Dict],
        topic: Optional[str]
    ) -> str:
        """
        Create AI prompt for sentiment analysis.

        Args:
            news_data: List of news data (sorted and limited).
            topic: Topic keyword.

        Returns:
            Formatted AI prompt string.
        """
        # Group by platform
        platform_news = defaultdict(list)
        for item in news_data:
            platform_news[item["platform"]].append({
                "title": item["title"],
                "date": item.get("date", "")
            })

        # Build prompt
        prompt_parts = []

        # 1. Task Instructions
        if topic:
            prompt_parts.append(f"Please analyze the sentiment of the following news titles regarding '{topic}'.")
        else:
            prompt_parts.append("Please analyze the sentiment of the following news titles.")

        prompt_parts.append("")
        prompt_parts.append("Analysis Requirements:")
        prompt_parts.append("1. Identify the sentiment of each news item (Positive/Negative/Neutral).")
        prompt_parts.append("2. Calculate the count and percentage for each sentiment category.")
        prompt_parts.append("3. Analyze sentiment differences across different platforms.")
        prompt_parts.append("4. Summarize the overall sentiment trend.")
        prompt_parts.append("5. List typical examples of positive and negative news.")
        prompt_parts.append("")

        # 2. Data Overview
        prompt_parts.append(f"Data Overview:")
        prompt_parts.append(f"- Total News Items: {len(news_data)}")
        prompt_parts.append(f"- Covered Platforms: {len(platform_news)}")

        # Time Range
        dates = set(item.get("date", "") for item in news_data if item.get("date"))
        if dates:
            date_list = sorted(dates)
            if len(date_list) == 1:
                prompt_parts.append(f"- Date Range: {date_list[0]}")
            else:
                prompt_parts.append(f"- Date Range: {date_list[0]} to {date_list[-1]}")

        prompt_parts.append("")

        # 3. News List by Platform
        prompt_parts.append("News List (Grouped by Platform, Sorted by Importance):")
        prompt_parts.append("")

        for platform, items in sorted(platform_news.items()):
            prompt_parts.append(f"【{platform}】({len(items)} items)")
            for i, item in enumerate(items, 1):
                title = item["title"]
                date_str = f" [{item['date']}]" if item.get("date") else ""
                prompt_parts.append(f"{i}. {title}{date_str}")
            prompt_parts.append("")

        # 4. Output Format
        prompt_parts.append("Please output the analysis result in the following format:")
        prompt_parts.append("")
        prompt_parts.append("## Sentiment Distribution")
        prompt_parts.append("- Positive: XX items (XX%)")
        prompt_parts.append("- Negative: XX items (XX%)")
        prompt_parts.append("- Neutral: XX items (XX%)")
        prompt_parts.append("")
        prompt_parts.append("## Platform Sentiment Comparison")
        prompt_parts.append("[Sentiment differences across platforms]")
        prompt_parts.append("")
        prompt_parts.append("## Overall Sentiment Trend")
        prompt_parts.append("[Overall analysis and key findings]")
        prompt_parts.append("")
        prompt_parts.append("## Typical Samples")
        prompt_parts.append("Positive News Samples:")
        prompt_parts.append("[List 3-5 items]")
        prompt_parts.append("")
        prompt_parts.append("Negative News Samples:")
        prompt_parts.append("[List 3-5 items]")

        return "\n".join(prompt_parts)

    def find_similar_news(
        self,
        reference_title: str,
        threshold: float = 0.6,
        limit: int = 50,
        include_url: bool = False
    ) -> Dict:
        """
        Find Similar News - Find related news based on title similarity.

        Args:
            reference_title: The title to compare against.
            threshold: Similarity threshold (between 0 and 1).
            limit: Limit the number of returned items, default 50.
            include_url: Whether to include URL links, default False.

        Returns:
            List of similar news items.
        """
        try:
            # Validate parameters
            reference_title = validate_keyword(reference_title)

            if not 0 <= threshold <= 1:
                raise InvalidParameterError(
                    "threshold must be between 0 and 1",
                    suggestion="Recommended value: 0.5-0.8"
                )

            limit = validate_limit(limit, default=50)

            # Read data
            all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date()

            # Calculate similarity
            similar_items = []

            for platform_id, titles in all_titles.items():
                platform_name = id_to_name.get(platform_id, platform_id)

                for title, info in titles.items():
                    if title == reference_title:
                        continue

                    # Calculate similarity
                    similarity = self._calculate_similarity(reference_title, title)

                    if similarity >= threshold:
                        news_item = {
                            "title": title,
                            "platform": platform_id,
                            "platform_name": platform_name,
                            "similarity": round(similarity, 3),
                            "rank": info["ranks"][0] if info["ranks"] else 0
                        }

                        # Conditionally add URL fields
                        if include_url:
                            news_item["url"] = info.get("url", "")

                        similar_items.append(news_item)

            # Sort by similarity
            similar_items.sort(key=lambda x: x["similarity"], reverse=True)

            # Limit quantity
            result_items = similar_items[:limit]

            if not result_items:
                raise DataNotFoundError(
                    f"No news found with similarity over {threshold}",
                    suggestion="Please lower the similarity threshold or try a different title."
                )

            result = {
                "success": True,
                "summary": {
                    "total_found": len(similar_items),
                    "returned_count": len(result_items),
                    "requested_limit": limit,
                    "threshold": threshold,
                    "reference_title": reference_title
                },
                "similar_news": result_items
            }

            if len(similar_items) < limit:
                result["note"] = f"Only {len(similar_items)} similar items found with threshold {threshold}"

            return result

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

    def search_by_entity(
        self,
        entity: str,
        entity_type: Optional[str] = None,
        limit: int = 50,
        sort_by_weight: bool = True
    ) -> Dict:
        """
        Entity Recognition Search - Search for news containing specific People/Locations/Organizations.

        Args:
            entity: Entity name.
            entity_type: Entity type (person/location/organization), optional.
            limit: Limit returned items, default 50.
            sort_by_weight: Sort by weight, default True.

        Returns:
            List of entity-related news.
        """
        try:
            # Validate parameters
            entity = validate_keyword(entity)
            limit = validate_limit(limit, default=50)

            if entity_type and entity_type not in ["person", "location", "organization"]:
                raise InvalidParameterError(
                    f"Invalid entity type: {entity_type}",
                    suggestion="Supported types: person, location, organization"
                )

            # Read data
            all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date()

            # Search for news containing the entity
            related_news = []
            entity_context = Counter()  # Count context words around the entity

            for platform_id, titles in all_titles.items():
                platform_name = id_to_name.get(platform_id, platform_id)

                for title, info in titles.items():
                    if entity in title:
                        url = info.get("url", "")
                        mobile_url = info.get("mobileUrl", "")
                        ranks = info.get("ranks", [])
                        count = len(ranks)

                        related_news.append({
                            "title": title,
                            "platform": platform_id,
                            "platform_name": platform_name,
                            "url": url,
                            "mobileUrl": mobile_url,
                            "ranks": ranks,
                            "count": count,
                            "rank": ranks[0] if ranks else 999
                        })

                        # Extract context keywords
                        keywords = self._extract_keywords(title)
                        entity_context.update(keywords)

            if not related_news:
                raise DataNotFoundError(
                    f"No news found containing entity '{entity}'",
                    suggestion="Please try another entity name."
                )

            # Remove the entity itself from context keywords
            if entity in entity_context:
                del entity_context[entity]

            # Sort
            if sort_by_weight:
                related_news.sort(
                    key=lambda x: calculate_news_weight(x),
                    reverse=True
                )
            else:
                related_news.sort(key=lambda x: x["rank"])

            # Limit
            result_news = related_news[:limit]

            return {
                "success": True,
                "entity": entity,
                "entity_type": entity_type or "auto",
                "related_news": result_news,
                "total_found": len(related_news),
                "returned_count": len(result_news),
                "sorted_by_weight": sort_by_weight,
                "related_keywords": [
                    {"keyword": k, "count": v}
                    for k, v in entity_context.most_common(10)
                ]
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

    def generate_summary_report(
        self,
        report_type: str = "daily",
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Daily/Weekly Summary Generator - Automatically generate hot topic summary reports.

        Args:
            report_type: Report type (daily/weekly).
            date_range: Custom date range (optional).

        Returns:
            Summary report in Markdown format.

        Examples:
            - "Generate today's news summary report"
            - "Give me a weekly hot topic summary"
        """
        try:
            # Validate parameters
            if report_type not in ["daily", "weekly"]:
                raise InvalidParameterError(
                    f"Invalid report type: {report_type}",
                    suggestion="Supported types: daily, weekly"
                )

            # Determine date range
            if date_range:
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                if report_type == "daily":
                    start_date = end_date = datetime.now()
                else:  # weekly
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=6)

            # Collect data
            all_keywords = Counter()
            all_platforms_news = defaultdict(int)
            all_titles_list = []

            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)
                        all_platforms_news[platform_name] += len(titles)

                        for title in titles.keys():
                            all_titles_list.append({
                                "title": title,
                                "platform": platform_name,
                                "date": current_date.strftime("%Y-%m-%d")
                            })

                            # Extract keywords
                            keywords = self._extract_keywords(title)
                            all_keywords.update(keywords)

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # Generate Report
            report_title = f"{'Daily' if report_type == 'daily' else 'Weekly'} News Summary"
            date_str = f"{start_date.strftime('%Y-%m-%d')}" if report_type == "daily" else f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

            # Build Markdown
            markdown = f"""# {report_title}

**Report Date**: {date_str}
**Generated At**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 Data Overview

- **Total News**: {len(all_titles_list)}
- **Covered Platforms**: {len(all_platforms_news)}
- **Hot Keywords**: {len(all_keywords)}

## 🔥 TOP 10 Hot Topics

"""

            # Add TOP 10 Keywords
            for i, (keyword, count) in enumerate(all_keywords.most_common(10), 1):
                markdown += f"{i}. **{keyword}** - {count} mentions\n"

            # Platform Activity
            markdown += "\n## 📱 Platform Activity\n\n"
            sorted_platforms = sorted(all_platforms_news.items(), key=lambda x: x[1], reverse=True)

            for platform, count in sorted_platforms:
                markdown += f"- **{platform}**: {count} items\n"

            # Trends (if weekly)
            if report_type == "weekly":
                markdown += "\n## 📈 Trend Analysis\n\n"
                markdown += "Sustained hot topics this week (samples):\n\n"

                # Simple trend analysis
                top_keywords = [kw for kw, _ in all_keywords.most_common(5)]
                for keyword in top_keywords:
                    markdown += f"- **{keyword}**: Sustained Hotspot\n"

            # News Samples
            markdown += "\n## 📰 Selected News Samples\n\n"

            # Deterministic selection: Sort by title weight
            if all_titles_list:
                news_with_scores = []
                for news in all_titles_list:
                    # Simple weight: count of TOP keyword occurrences
                    score = 0
                    title_lower = news['title'].lower()
                    for keyword, count in all_keywords.most_common(10):
                        if keyword.lower() in title_lower:
                            score += count
                    news_with_scores.append((news, score))

                # Sort by score desc, then title alphabetically
                news_with_scores.sort(key=lambda x: (-x[1], x[0]['title']))

                # Take top 5
                sample_news = [item[0] for item in news_with_scores[:5]]

                for news in sample_news:
                    markdown += f"- [{news['platform']}] {news['title']}\n"

            markdown += "\n---\n\n*Generated automatically by SignalForge MCP*\n"

            return {
                "success": True,
                "report_type": report_type,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "markdown_report": markdown,
                "statistics": {
                    "total_news": len(all_titles_list),
                    "platforms_count": len(all_platforms_news),
                    "keywords_count": len(all_keywords),
                    "top_keyword": all_keywords.most_common(1)[0] if all_keywords else None
                }
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

    def get_platform_activity_stats(
        self,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Platform Activity Stats - Statistics on platform posting frequency and active times.

        Args:
            date_range: Date range (optional).

        Returns:
            Platform activity statistics.
        """
        try:
            # Validate and determine date range
            date_range_tuple = validate_date_range(date_range)
            if date_range_tuple:
                start_date, end_date = date_range_tuple
            else:
                start_date = end_date = datetime.now()

            # Stats container
            platform_activity = defaultdict(lambda: {
                "total_updates": 0,
                "days_active": set(),
                "news_count": 0,
                "hourly_distribution": Counter()
            })

            # Iterate dates
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, timestamps = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        platform_activity[platform_name]["news_count"] += len(titles)
                        platform_activity[platform_name]["days_active"].add(current_date.strftime("%Y-%m-%d"))
                        platform_activity[platform_name]["total_updates"] += len(timestamps)

                        # Time distribution from filenames
                        for filename in timestamps.keys():
                            match = re.match(r'(\d{2})(\d{2})\.txt', filename)
                            if match:
                                hour = int(match.group(1))
                                platform_activity[platform_name]["hourly_distribution"][hour] += 1

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # Convert to serializable format
            result_activity = {}
            for platform, stats in platform_activity.items():
                days_count = len(stats["days_active"])
                avg_news_per_day = stats["news_count"] / days_count if days_count > 0 else 0

                most_active_hours = stats["hourly_distribution"].most_common(3)

                result_activity[platform] = {
                    "total_updates": stats["total_updates"],
                    "news_count": stats["news_count"],
                    "days_active": days_count,
                    "avg_news_per_day": round(avg_news_per_day, 2),
                    "most_active_hours": [
                        {"hour": f"{hour:02d}:00", "count": count}
                        for hour, count in most_active_hours
                    ],
                    "activity_score": round(stats["news_count"] / max(days_count, 1), 2)
                }

            # Sort by activity score
            sorted_platforms = sorted(
                result_activity.items(),
                key=lambda x: x[1]["activity_score"],
                reverse=True
            )

            return {
                "success": True,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "platform_activity": dict(sorted_platforms),
                "most_active_platform": sorted_platforms[0][0] if sorted_platforms else None,
                "total_platforms": len(result_activity)
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

    def analyze_topic_lifecycle(
        self,
        topic: str,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        Topic Lifecycle Analysis - Track the full cycle of a topic from emergence to disappearance.

        Args:
            topic: Topic keyword.
            date_range: Date range (optional). Default last 7 days.

        Returns:
            Topic lifecycle analysis result.
        """
        try:
            topic = validate_keyword(topic)

            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=6)

            lifecycle_data = []
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )
                    count = 0
                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            if topic.lower() in title.lower():
                                count += 1
                    lifecycle_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": count
                    })
                except DataNotFoundError:
                    lifecycle_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": 0
                    })
                current_date += timedelta(days=1)

            total_days = (end_date - start_date).days + 1
            counts = [item["count"] for item in lifecycle_data]

            if not any(counts):
                time_desc = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
                raise DataNotFoundError(
                    f"Topic '{topic}' not found in range {time_desc}",
                    suggestion="Please try another topic or expand the time range."
                )

            first_appearance = next((item["date"] for item in lifecycle_data if item["count"] > 0), None)
            last_appearance = next((item["date"] for item in reversed(lifecycle_data) if item["count"] > 0), None)

            max_count = max(counts)
            peak_index = counts.index(max_count)
            peak_date = lifecycle_data[peak_index]["date"]

            non_zero_counts = [c for c in counts if c > 0]
            avg_count = sum(non_zero_counts) / len(non_zero_counts) if non_zero_counts else 0

            # Determine Lifecycle Stage
            recent_counts = counts[-3:]
            early_counts = counts[:3]

            if sum(recent_counts) > sum(early_counts):
                lifecycle_stage = "Rising Phase"
            elif sum(recent_counts) < sum(early_counts) * 0.5:
                lifecycle_stage = "Recession Phase"
            elif max_count in recent_counts:
                lifecycle_stage = "Explosion Phase"
            else:
                lifecycle_stage = "Stable Phase"

            # Classify Topic Type
            active_days = sum(1 for c in counts if c > 0)

            if active_days <= 2 and max_count > avg_count * 2:
                topic_type = "Flash in the pan"
            elif active_days >= total_days * 0.6:
                topic_type = "Sustained Hotspot"
            else:
                topic_type = "Periodic Hotspot"

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                    "total_days": total_days
                },
                "lifecycle_data": lifecycle_data,
                "analysis": {
                    "first_appearance": first_appearance,
                    "last_appearance": last_appearance,
                    "peak_date": peak_date,
                    "peak_count": max_count,
                    "active_days": active_days,
                    "avg_daily_mentions": round(avg_count, 2),
                    "lifecycle_stage": lifecycle_stage,
                    "topic_type": topic_type
                }
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

    def detect_viral_topics(
        self,
        threshold: float = 3.0,
        time_window: int = 24
    ) -> Dict:
        """
        Viral Topic Detection - Identify suddenly exploding topics.

        Args:
            threshold: Sudden increase multiplier threshold.
            time_window: Detection time window (hours).

        Returns:
            List of viral topics.
        """
        try:
            if threshold < 1.0:
                raise InvalidParameterError(
                    "threshold must be >= 1.0",
                    suggestion="Recommended: 2.0-5.0"
                )
            time_window = validate_limit(time_window, default=24, max_limit=72)

            # Read current and previous data
            current_all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

            yesterday = datetime.now() - timedelta(days=1)
            try:
                previous_all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(date=yesterday)
            except DataNotFoundError:
                previous_all_titles = {}

            # Count keywords
            current_keywords = Counter()
            current_keyword_titles = defaultdict(list)
            for _, titles in current_all_titles.items():
                for title in titles.keys():
                    keywords = self._extract_keywords(title)
                    current_keywords.update(keywords)
                    for kw in keywords:
                        current_keyword_titles[kw].append(title)

            previous_keywords = Counter()
            for _, titles in previous_all_titles.items():
                for title in titles.keys():
                    keywords = self._extract_keywords(title)
                    previous_keywords.update(keywords)

            # Detect viral
            viral_topics = []
            for keyword, current_count in current_keywords.items():
                previous_count = previous_keywords.get(keyword, 0)

                if previous_count == 0:
                    # New topic
                    if current_count >= 5:
                        growth_rate = float('inf')
                        is_viral = True
                    else:
                        continue
                else:
                    growth_rate = current_count / previous_count
                    is_viral = growth_rate >= threshold

                if is_viral:
                    viral_topics.append({
                        "keyword": keyword,
                        "current_count": current_count,
                        "previous_count": previous_count,
                        "growth_rate": round(growth_rate, 2) if growth_rate != float('inf') else "New Topic",
                        "sample_titles": current_keyword_titles[keyword][:3],
                        "alert_level": "High" if growth_rate > threshold * 2 else "Medium"
                    })

            viral_topics.sort(
                key=lambda x: x["current_count"] if x["growth_rate"] == "New Topic" else x["growth_rate"],
                reverse=True
            )

            if not viral_topics:
                return {
                    "success": True,
                    "viral_topics": [],
                    "total_detected": 0,
                    "message": f"No topics detected with growth rate > {threshold}"
                }

            return {
                "success": True,
                "viral_topics": viral_topics,
                "total_detected": len(viral_topics),
                "threshold": threshold,
                "time_window": time_window,
                "detection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

    def predict_trending_topics(
        self,
        lookahead_hours: int = 6,
        confidence_threshold: float = 0.7
    ) -> Dict:
        """
        Topic Prediction - Predict future hotspots based on historical data.

        Args:
            lookahead_hours: Hours to predict ahead.
            confidence_threshold: Confidence threshold.

        Returns:
            Predicted potential topics.
        """
        try:
            lookahead_hours = validate_limit(lookahead_hours, default=6, max_limit=48)

            if not 0 <= confidence_threshold <= 1:
                raise InvalidParameterError(
                    "confidence_threshold must be between 0 and 1",
                    suggestion="Recommended: 0.6-0.8"
                )

            keyword_trends = defaultdict(list)

            # Collect past 3 days data
            for days_ago in range(3, 0, -1):
                date = datetime.now() - timedelta(days=days_ago)
                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(date=date)
                    keywords_count = Counter()
                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            keywords = self._extract_keywords(title)
                            keywords_count.update(keywords)
                    for keyword, count in keywords_count.items():
                        keyword_trends[keyword].append(count)
                except DataNotFoundError:
                    pass

            # Add today's data
            try:
                all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()
                keywords_count = Counter()
                keyword_titles = defaultdict(list)
                for _, titles in all_titles.items():
                    for title in titles.keys():
                        keywords = self._extract_keywords(title)
                        keywords_count.update(keywords)
                        for kw in keywords:
                            keyword_titles[kw].append(title)
                for keyword, count in keywords_count.items():
                    keyword_trends[keyword].append(count)
            except DataNotFoundError:
                raise DataNotFoundError("No data found for today", suggestion="Wait for crawler completion.")

            predicted_topics = []
            for keyword, trend_data in keyword_trends.items():
                if len(trend_data) < 2:
                    continue

                # Simple Linear Trend
                recent_value = trend_data[-1]
                previous_value = trend_data[-2] if len(trend_data) >= 2 else 0

                if previous_value == 0:
                    if recent_value >= 3:
                        growth_rate = 1.0
                    else:
                        continue
                else:
                    growth_rate = (recent_value - previous_value) / previous_value

                if growth_rate > 0.3:  # >30% growth
                    # Calculate confidence
                    if len(trend_data) >= 3:
                        is_consistent = all(trend_data[i] <= trend_data[i+1] for i in range(len(trend_data)-1))
                        confidence = 0.9 if is_consistent else 0.7
                    else:
                        confidence = 0.6

                    if confidence >= confidence_threshold:
                        predicted_topics.append({
                            "keyword": keyword,
                            "current_count": recent_value,
                            "growth_rate": round(growth_rate * 100, 2),
                            "confidence": round(confidence, 2),
                            "trend_data": trend_data,
                            "prediction": "Rising trend, potential hotspot",
                            "sample_titles": keyword_titles.get(keyword, [])[:3]
                        })

            predicted_topics.sort(key=lambda x: (x["confidence"], x["growth_rate"]), reverse=True)

            return {
                "success": True,
                "predicted_topics": predicted_topics[:20],
                "total_predicted": len(predicted_topics),
                "lookahead_hours": lookahead_hours,
                "confidence_threshold": confidence_threshold,
                "prediction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "note": "Predictions based on history; actual results may vary."
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

    # ==================== Helper Methods ====================

    def _extract_keywords(self, title: str, min_length: int = 2) -> List[str]:
        """
        Extract keywords from title.

        Args:
            title: Title text.
            min_length: Minimum keyword length.

        Returns:
            List of keywords.
        """
        # Remove URLs and special characters
        title = re.sub(r'http[s]?://\S+', '', title)
        # Keep alphanumeric and some basic chars, replace others with space
        title = re.sub(r'[^\w\s]', ' ', title)

        # Split by whitespace and common punctuation
        words = re.split(r'[\s,.\?!]+', title)

        # English Stopwords (Basic set)
        stopwords = {
            'the', 'a', 'an', 'in', 'on', 'at', 'of', 'for', 'to', 'is', 'are', 
            'was', 'were', 'be', 'been', 'this', 'that', 'it', 'and', 'or', 
            'but', 'not', 'with', 'as', 'by', 'from', 'top', 'hot', 'new', 'news'
        }

        keywords = [
            word.strip() for word in words
            if word.strip() and len(word.strip()) >= min_length and word.lower().strip() not in stopwords
        ]

        return keywords

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.

        Args:
            text1: Text 1.
            text2: Text 2.

        Returns:
            Similarity score (0-1).
        """
        return SequenceMatcher(None, text1, text2).ratio()

    def _find_unique_topics(self, platform_stats: Dict) -> Dict[str, List[str]]:
        """
        Find unique hot topics for each platform.

        Args:
            platform_stats: Platform statistics data.

        Returns:
            Dictionary of unique topics per platform.
        """
        unique_topics = {}

        # Get TOP keywords for each platform
        platform_keywords = {}
        for platform, stats in platform_stats.items():
            top_keywords = set([kw for kw, _ in stats["top_keywords"].most_common(10)])
            platform_keywords[platform] = top_keywords

        # Find unique keywords
        for platform, keywords in platform_keywords.items():
            # Find keywords present in all other platforms
            other_keywords = set()
            for other_platform, other_kws in platform_keywords.items():
                if other_platform != platform:
                    other_keywords.update(other_kws)

            # Identify unique ones
            unique = keywords - other_keywords
            if unique:
                unique_topics[platform] = list(unique)[:5]  # Max 5

        return unique_topics