"""
Intelligent News Search Tools

Provides advanced search capabilities including fuzzy search, link retrieval, 
and historical related news retrieval.
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple, Set

from ..services.data_service import DataService
from ..utils.validators import validate_keyword, validate_limit
from ..utils.errors import MCPError, InvalidParameterError, DataNotFoundError


class SearchTools:
    """Intelligent News Search Tools Class"""

    def __init__(self, project_root: str = None):
        """
        Initialize the intelligent search tools.

        Args:
            project_root: The root directory of the project.
        """
        self.data_service = DataService(project_root)
        
        # UPGRADE: Comprehensive English Stopwords List
        self.stopwords: Set[str] = {
            'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
            'when', 'where', 'how', 'which', 'who', 'whom', 'this', 'that', 'these',
            'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves',
            'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
            'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
            'they', 'them', 'their', 'theirs', 'themselves', 'to', 'from', 'up',
            'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
            'then', 'once', 'here', 'there', 'why', 'all', 'any', 'both', 'each',
            'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
            'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will',
            'just', 'should', 'now', 'news', 'report', 'today', 'daily'
        }

    def search_news_unified(
        self,
        query: str,
        search_mode: str = "keyword",
        date_range: Optional[Dict[str, str]] = None,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        sort_by: str = "relevance",
        threshold: float = 0.6,
        include_url: bool = False
    ) -> Dict:
        """
        Unified News Search Tool - Integrates multiple search modes.

        Args:
            query: Search content (Required) - Keyword, content fragment, or entity name.
            search_mode: Search mode options:
                - "keyword": Exact keyword matching (Default).
                - "fuzzy": Fuzzy content matching (uses similarity algorithms).
                - "entity": Entity name search (automatically sorted by weight).
            date_range: Date range (Optional).
                       - **Format**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **Default**: Queries "Today" if not specified.
            platforms: List of platforms to filter, e.g., ['zhihu', 'weibo'].
            limit: Limit the number of returned items. Default is 50.
            sort_by: Sorting method options:
                - "relevance": Sort by relevance score (Default).
                - "weight": Sort by news weight/rank.
                - "date": Sort by date.
            threshold: Similarity threshold (Valid only for 'fuzzy' mode), between 0-1. Default 0.6.
            include_url: Whether to include URL links. Default False (saves tokens).

        Returns:
            Dictionary containing search results.

        Examples:
            - search_news_unified(query="AI", search_mode="keyword")
            - search_news_unified(query="Tesla Price Cut", search_mode="fuzzy", threshold=0.4)
        """
        try:
            # Parameter Validation
            query = validate_keyword(query)

            if search_mode not in ["keyword", "fuzzy", "entity"]:
                raise InvalidParameterError(
                    f"Invalid search mode: {search_mode}",
                    suggestion="Supported modes: keyword, fuzzy, entity"
                )

            if sort_by not in ["relevance", "weight", "date"]:
                raise InvalidParameterError(
                    f"Invalid sort method: {sort_by}",
                    suggestion="Supported sorts: relevance, weight, date"
                )

            limit = validate_limit(limit, default=50)
            threshold = max(0.0, min(1.0, threshold))

            # Handle Date Range
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # If no date specified, use the latest available data date
                earliest, latest = self.data_service.get_available_date_range()

                if latest is None:
                    return {
                        "success": False,
                        "error": {
                            "code": "NO_DATA_AVAILABLE",
                            "message": "No available news data in the output directory.",
                            "suggestion": "Please run the crawler to generate data or check the output directory."
                        }
                    }

                # Use the latest available date
                start_date = end_date = latest

            # Collect all matches
            all_matches = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, id_to_name, timestamps = self.data_service.parser.read_all_titles_for_date(
                        date=current_date,
                        platform_ids=platforms
                    )

                    # Execute different logic based on search mode
                    if search_mode == "keyword":
                        matches = self._search_by_keyword_mode(
                            query, all_titles, id_to_name, current_date, include_url
                        )
                    elif search_mode == "fuzzy":
                        matches = self._search_by_fuzzy_mode(
                            query, all_titles, id_to_name, current_date, threshold, include_url
                        )
                    else:  # entity
                        matches = self._search_by_entity_mode(
                            query, all_titles, id_to_name, current_date, include_url
                        )

                    all_matches.extend(matches)

                except DataNotFoundError:
                    # No data for this date, continue
                    pass

                current_date += timedelta(days=1)

            if not all_matches:
                # Build context for error message
                earliest, latest = self.data_service.get_available_date_range()
                
                if start_date.date() == datetime.now().date() and start_date == end_date:
                    time_desc = "Today"
                elif start_date == end_date:
                    time_desc = start_date.strftime("%Y-%m-%d")
                else:
                    time_desc = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

                available_desc = "None"
                if earliest and latest:
                    available_desc = f"{earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}"

                message = f"No news found matching query. (Search Range: {time_desc}, Available Data: {available_desc})"

                return {
                    "success": True,
                    "results": [],
                    "total": 0,
                    "query": query,
                    "search_mode": search_mode,
                    "time_range": time_desc,
                    "message": message
                }

            # Unified Sorting Logic
            if sort_by == "relevance":
                all_matches.sort(key=lambda x: x.get("similarity_score", 1.0), reverse=True)
            elif sort_by == "weight":
                from .analytics import calculate_news_weight
                all_matches.sort(key=lambda x: calculate_news_weight(x), reverse=True)
            elif sort_by == "date":
                all_matches.sort(key=lambda x: x.get("date", ""), reverse=True)

            # Limit Results
            results = all_matches[:limit]

            # Build Time Range Description
            if start_date.date() == datetime.now().date() and start_date == end_date:
                time_range_desc = "Today"
            elif start_date == end_date:
                time_range_desc = start_date.strftime("%Y-%m-%d")
            else:
                time_range_desc = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

            result = {
                "success": True,
                "summary": {
                    "total_found": len(all_matches),
                    "returned_count": len(results),
                    "requested_limit": limit,
                    "search_mode": search_mode,
                    "query": query,
                    "platforms": platforms or "All Platforms",
                    "time_range": time_range_desc,
                    "sort_by": sort_by
                },
                "results": results
            }

            if search_mode == "fuzzy":
                result["summary"]["threshold"] = threshold
                if len(all_matches) < limit:
                    result["note"] = f"In fuzzy mode, threshold {threshold} yielded only {len(all_matches)} results."

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

    def _search_by_keyword_mode(
        self,
        query: str,
        all_titles: Dict,
        id_to_name: Dict,
        current_date: datetime,
        include_url: bool
    ) -> List[Dict]:
        """Keyword Search Mode (Exact Match)"""
        matches = []
        query_lower = query.lower()

        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                if query_lower in title.lower():
                    news_item = {
                        "title": title,
                        "platform": platform_id,
                        "platform_name": platform_name,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "similarity_score": 1.0,
                        "ranks": info.get("ranks", []),
                        "count": len(info.get("ranks", [])),
                        "rank": info["ranks"][0] if info["ranks"] else 999
                    }

                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobileUrl"] = info.get("mobileUrl", "")

                    matches.append(news_item)

        return matches

    def _search_by_fuzzy_mode(
        self,
        query: str,
        all_titles: Dict,
        id_to_name: Dict,
        current_date: datetime,
        threshold: float,
        include_url: bool
    ) -> List[Dict]:
        """Fuzzy Search Mode (Similarity Algorithm)"""
        matches = []

        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                is_match, similarity = self._fuzzy_match(query, title, threshold)

                if is_match:
                    news_item = {
                        "title": title,
                        "platform": platform_id,
                        "platform_name": platform_name,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "similarity_score": round(similarity, 4),
                        "ranks": info.get("ranks", []),
                        "count": len(info.get("ranks", [])),
                        "rank": info["ranks"][0] if info["ranks"] else 999
                    }

                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobileUrl"] = info.get("mobileUrl", "")

                    matches.append(news_item)

        return matches

    def _search_by_entity_mode(
        self,
        query: str,
        all_titles: Dict,
        id_to_name: Dict,
        current_date: datetime,
        include_url: bool
    ) -> List[Dict]:
        """Entity Search Mode"""
        matches = []

        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # Case-insensitive entity check for English support
                if query.lower() in title.lower():
                    news_item = {
                        "title": title,
                        "platform": platform_id,
                        "platform_name": platform_name,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "similarity_score": 1.0,
                        "ranks": info.get("ranks", []),
                        "count": len(info.get("ranks", [])),
                        "rank": info["ranks"][0] if info["ranks"] else 999
                    }

                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobileUrl"] = info.get("mobileUrl", "")

                    matches.append(news_item)

        return matches

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using SequenceMatcher."""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _fuzzy_match(self, query: str, text: str, threshold: float = 0.3) -> Tuple[bool, float]:
        """
        UPGRADED: Hybrid Fuzzy Matching.
        Combines exact string containment, SequenceMatcher, and Jaccard Keyword Overlap.

        Args:
            query: Query text.
            text: Text to match against.
            threshold: Match threshold.

        Returns:
            (is_match, similarity_score)
        """
        query_lower = query.lower()
        text_lower = text.lower()

        # 1. Direct Containment (Highest Priority)
        if query_lower in text_lower:
            return True, 1.0

        # 2. Sequence Similarity (Levenshtein-like)
        seq_similarity = self._calculate_similarity(query_lower, text_lower)
        if seq_similarity >= threshold:
            return True, seq_similarity

        # 3. Keyword Overlap (Jaccard Index)
        query_keywords = set(self._extract_keywords(query_lower))
        text_keywords = set(self._extract_keywords(text_lower))

        if not query_keywords or not text_keywords:
            return False, 0.0

        common_words = query_keywords & text_keywords
        keyword_overlap = len(common_words) / len(query_keywords)

        # 4. Hybrid Score
        # If keyword overlap is significant (>50%), boost the similarity score
        if keyword_overlap >= 0.5:
            return True, max(seq_similarity, keyword_overlap)
        
        # If overlap is non-zero but small, weighted average
        if keyword_overlap > 0:
            hybrid_score = (seq_similarity * 0.4) + (keyword_overlap * 0.6)
            if hybrid_score >= threshold:
                return True, hybrid_score

        return False, seq_similarity

    def _extract_keywords(self, text: str, min_length: int = 2) -> List[str]:
        """
        UPGRADED: Extract keywords from text.
        Improved regex for English support (alphanumeric).

        Args:
            text: Input text.
            min_length: Minimum word length.

        Returns:
            List of keywords.
        """
        # Remove URLs and bracketed content
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'\[.*?\]', '', text)

        # Extract words (Allows apostrophes for contractions like "don't", "Tesla's")
        words = re.findall(r"\b[a-zA-Z0-9']+\b", text.lower())

        # Filter stopwords and short words
        keywords = [
            word for word in words
            if len(word) >= min_length and word not in self.stopwords
        ]

        return keywords

    def _calculate_keyword_overlap(self, keywords1: List[str], keywords2: List[str]) -> float:
        """Calculate Jaccard similarity between two keyword lists."""
        if not keywords1 or not keywords2:
            return 0.0

        set1 = set(keywords1)
        set2 = set(keywords2)

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def search_related_news_history(
        self,
        reference_text: str,
        time_preset: str = "yesterday",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        threshold: float = 0.4,
        limit: int = 50,
        include_url: bool = False
    ) -> Dict:
        """
        Search for news related to a given text in historical data.

        Args:
            reference_text: Reference news title or content.
            time_preset: Time range preset:
                - "yesterday": Yesterday
                - "last_week": Last week (7 days)
                - "last_month": Last month (30 days)
                - "custom": Custom date range (requires start_date and end_date)
            start_date: Custom start date (Required if time_preset="custom").
            end_date: Custom end date (Required if time_preset="custom").
            threshold: Similarity threshold (0-1), default 0.4.
            limit: Limit returned items, default 50.
            include_url: Whether to include URL links, default False.

        Returns:
            Dictionary containing related news list.
        """
        try:
            # Parameter Validation
            reference_text = validate_keyword(reference_text)
            threshold = max(0.0, min(1.0, threshold))
            limit = validate_limit(limit, default=50)

            # Determine Date Range
            today = datetime.now()

            if time_preset == "yesterday":
                search_start = today - timedelta(days=1)
                search_end = today - timedelta(days=1)
            elif time_preset == "last_week":
                search_start = today - timedelta(days=7)
                search_end = today - timedelta(days=1)
            elif time_preset == "last_month":
                search_start = today - timedelta(days=30)
                search_end = today - timedelta(days=1)
            elif time_preset == "custom":
                if not start_date or not end_date:
                    raise InvalidParameterError(
                        "Custom time range requires start_date and end_date",
                        suggestion="Please provide start_date and end_date parameters"
                    )
                search_start = start_date
                search_end = end_date
            else:
                raise InvalidParameterError(
                    f"Unsupported time preset: {time_preset}",
                    suggestion="Use 'yesterday', 'last_week', 'last_month', or 'custom'"
                )

            # Extract Keywords from Reference Text
            reference_keywords = self._extract_keywords(reference_text)

            if not reference_keywords:
                raise InvalidParameterError(
                    "Could not extract keywords from reference text",
                    suggestion="Please provide more detailed text content."
                )

            # Collect Related News
            all_related_news = []
            current_date = search_start

            while current_date <= search_end:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(current_date)

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        for title, info in titles.items():
                            # 1. Text Similarity
                            title_similarity = self._calculate_similarity(reference_text, title)

                            # 2. Keyword Overlap
                            title_keywords = self._extract_keywords(title)
                            keyword_overlap = self._calculate_keyword_overlap(
                                reference_keywords,
                                title_keywords
                            )

                            # 3. Combined Score (70% Keywords + 30% String Distance)
                            combined_score = (keyword_overlap * 0.7) + (title_similarity * 0.3)

                            if combined_score >= threshold:
                                news_item = {
                                    "title": title,
                                    "platform": platform_id,
                                    "platform_name": platform_name,
                                    "date": current_date.strftime("%Y-%m-%d"),
                                    "similarity_score": round(combined_score, 4),
                                    "keyword_overlap": round(keyword_overlap, 4),
                                    "text_similarity": round(title_similarity, 4),
                                    "common_keywords": list(set(reference_keywords) & set(title_keywords)),
                                    "rank": info["ranks"][0] if info["ranks"] else 0
                                }

                                if include_url:
                                    news_item["url"] = info.get("url", "")
                                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                                all_related_news.append(news_item)

                except DataNotFoundError:
                    pass
                except Exception as e:
                    print(f"Warning: Error processing date {current_date.strftime('%Y-%m-%d')}: {e}")

                current_date += timedelta(days=1)

            if not all_related_news:
                return {
                    "success": True,
                    "results": [],
                    "total": 0,
                    "query": reference_text,
                    "time_preset": time_preset,
                    "date_range": {
                        "start": search_start.strftime("%Y-%m-%d"),
                        "end": search_end.strftime("%Y-%m-%d")
                    },
                    "message": "No related news found."
                }

            # Sort by Similarity
            all_related_news.sort(key=lambda x: x["similarity_score"], reverse=True)

            # Limit Results
            results = all_related_news[:limit]

            # Statistics
            platform_distribution = Counter([news["platform"] for news in all_related_news])
            date_distribution = Counter([news["date"] for news in all_related_news])

            result = {
                "success": True,
                "summary": {
                    "total_found": len(all_related_news),
                    "returned_count": len(results),
                    "requested_limit": limit,
                    "threshold": threshold,
                    "reference_text": reference_text,
                    "reference_keywords": reference_keywords,
                    "time_preset": time_preset,
                    "date_range": {
                        "start": search_start.strftime("%Y-%m-%d"),
                        "end": search_end.strftime("%Y-%m-%d")
                    }
                },
                "results": results,
                "statistics": {
                    "platform_distribution": dict(platform_distribution),
                    "date_distribution": dict(date_distribution),
                    "avg_similarity": round(
                        sum([news["similarity_score"] for news in all_related_news]) / len(all_related_news),
                        4
                    ) if all_related_news else 0.0
                }
            }

            if len(all_related_news) < limit:
                result["note"] = f"Only found {len(all_related_news)} items with relevance threshold {threshold}."

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