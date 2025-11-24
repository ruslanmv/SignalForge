"""
File Parser Service

Provides parsing functionality for TXT format news data and YAML configuration files.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

import yaml

from ..utils.errors import FileParseError, DataNotFoundError
from .cache_service import get_cache


class ParserService:
    """File Parser Service Class"""

    def __init__(self, project_root: str = None):
        """
        Initialize the parser service.

        Args:
            project_root: Project root directory. Defaults to the parent of the current directory's parent.
        """
        if project_root is None:
            # Get the parent of the parent of the directory containing the current file
            current_file = Path(__file__)
            self.project_root = current_file.parent.parent.parent
        else:
            self.project_root = Path(project_root)

        # Initialize cache service
        self.cache = get_cache()

    @staticmethod
    def clean_title(title: str) -> str:
        """
        Clean title text.

        Args:
            title: Original title.

        Returns:
            Cleaned title.
        """
        # Remove excess whitespace
        title = re.sub(r'\s+', ' ', title)
        # Remove special characters
        title = title.strip()
        return title

    def parse_txt_file(self, file_path: Path) -> Tuple[Dict, Dict]:
        """
        Parse title data from a single TXT file.

        Args:
            file_path: Path to the TXT file.

        Returns:
            A tuple (titles_by_id, id_to_name)
            - titles_by_id: {platform_id: {title: {ranks, url, mobileUrl}}}
            - id_to_name: {platform_id: platform_name}

        Raises:
            FileParseError: If file parsing fails.
        """
        if not file_path.exists():
            raise FileParseError(str(file_path), "File does not exist")

        titles_by_id = {}
        id_to_name = {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                sections = content.split("\n\n")

                for section in sections:
                    if not section.strip() or "==== 以下ID请求失败 ====" in section:
                        continue

                    lines = section.strip().split("\n")
                    if len(lines) < 2:
                        continue

                    # Parse header: id | name or just id
                    header_line = lines[0].strip()
                    if " | " in header_line:
                        parts = header_line.split(" | ", 1)
                        source_id = parts[0].strip()
                        name = parts[1].strip()
                        id_to_name[source_id] = name
                    else:
                        source_id = header_line
                        id_to_name[source_id] = source_id

                    titles_by_id[source_id] = {}

                    # Parse title lines
                    for line in lines[1:]:
                        if line.strip():
                            try:
                                title_part = line.strip()
                                rank = None

                                # Extract rank
                                if ". " in title_part and title_part.split(". ")[0].isdigit():
                                    rank_str, title_part = title_part.split(". ", 1)
                                    rank = int(rank_str)

                                # Extract MOBILE URL
                                mobile_url = ""
                                if " [MOBILE:" in title_part:
                                    title_part, mobile_part = title_part.rsplit(" [MOBILE:", 1)
                                    if mobile_part.endswith("]"):
                                        mobile_url = mobile_part[:-1]

                                # Extract URL
                                url = ""
                                if " [URL:" in title_part:
                                    title_part, url_part = title_part.rsplit(" [URL:", 1)
                                    if url_part.endswith("]"):
                                        url = url_part[:-1]

                                title = self.clean_title(title_part.strip())
                                ranks = [rank] if rank is not None else [1]

                                titles_by_id[source_id][title] = {
                                    "ranks": ranks,
                                    "url": url,
                                    "mobileUrl": mobile_url,
                                }

                            except Exception as e:
                                # Ignore single line parsing errors
                                continue

        except Exception as e:
            raise FileParseError(str(file_path), str(e))

        return titles_by_id, id_to_name

    def get_date_folder_name(self, date: datetime = None) -> str:
        """
        Get date folder name.

        Args:
            date: Date object, defaults to today.

        Returns:
            Folder name, format: YYYY年MM月DD日 (YearMonthDay in Chinese format)
        """
        if date is None:
            date = datetime.now()
        # Using Chinese format for folder names as per existing system convention
        return date.strftime("%Y年%m月%d日")

    def read_all_titles_for_date(
        self,
        date: datetime = None,
        platform_ids: Optional[List[str]] = None
    ) -> Tuple[Dict, Dict, Dict]:
        """
        Read all title files for a specific date (with caching).

        Args:
            date: Date object, defaults to today.
            platform_ids: List of platform IDs, None means all platforms.

        Returns:
            A tuple (all_titles, id_to_name, all_timestamps)
            - all_titles: {platform_id: {title: {ranks, url, mobileUrl, ...}}}
            - id_to_name: {platform_id: platform_name}
            - all_timestamps: {filename: timestamp}

        Raises:
            DataNotFoundError: If data does not exist.
        """
        # Generate cache key
        date_str = self.get_date_folder_name(date)
        platform_key = ','.join(sorted(platform_ids)) if platform_ids else 'all'
        cache_key = f"read_all_titles:{date_str}:{platform_key}"

        # Try to get from cache
        # For historical data (not today), use longer cache time (1 hour)
        # For today's data, use shorter cache time (15 minutes) as new data might arrive
        is_today = (date is None) or (date.date() == datetime.now().date())
        ttl = 900 if is_today else 3600  # 15 mins vs 1 hour

        cached = self.cache.get(cache_key, ttl=ttl)
        if cached:
            return cached

        # Cache miss, read files
        date_folder = self.get_date_folder_name(date)
        txt_dir = self.project_root / "output" / date_folder / "txt"

        if not txt_dir.exists():
            raise DataNotFoundError(
                f"Data directory not found for {date_folder}",
                suggestion="Please run the crawler first or check if the date is correct."
            )

        all_titles = {}
        id_to_name = {}
        all_timestamps = {}

        # Read all txt files
        txt_files = sorted(txt_dir.glob("*.txt"))

        if not txt_files:
            raise DataNotFoundError(
                f"No data files in {date_folder}",
                suggestion="Please wait for the crawler task to complete."
            )

        for txt_file in txt_files:
            try:
                titles_by_id, file_id_to_name = self.parse_txt_file(txt_file)

                # Update id_to_name
                id_to_name.update(file_id_to_name)

                # Merge title data
                for platform_id, titles in titles_by_id.items():
                    # If platform filtering is specified
                    if platform_ids and platform_id not in platform_ids:
                        continue

                    if platform_id not in all_titles:
                        all_titles[platform_id] = {}

                    for title, info in titles.items():
                        if title in all_titles[platform_id]:
                            # Merge ranks
                            all_titles[platform_id][title]["ranks"].extend(info["ranks"])
                        else:
                            all_titles[platform_id][title] = info.copy()

                # Record file timestamp
                all_timestamps[txt_file.name] = txt_file.stat().st_mtime

            except Exception as e:
                # Ignore parsing errors for single files, continue processing others
                print(f"Warning: Failed to parse file {txt_file}: {e}")
                continue

        if not all_titles:
            raise DataNotFoundError(
                f"No valid data in {date_folder}",
                suggestion="Please check data file format or re-run the crawler."
            )

        # Cache result
        result = (all_titles, id_to_name, all_timestamps)
        self.cache.set(cache_key, result)

        return result

    def parse_yaml_config(self, config_path: str = None) -> dict:
        """
        Parse YAML configuration file.

        Args:
            config_path: Path to config file, defaults to config/config.yaml.

        Returns:
            Configuration dictionary.

        Raises:
            FileParseError: If config file parsing fails.
        """
        if config_path is None:
            config_path = self.project_root / "config" / "config.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileParseError(str(config_path), "Configuration file does not exist")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            return config_data
        except Exception as e:
            raise FileParseError(str(config_path), str(e))

    def parse_frequency_words(self, words_file: str = None) -> List[Dict]:
        """
        Parse keyword configuration file.

        Args:
            words_file: Path to keyword file, defaults to config/frequency_words.txt.

        Returns:
            List of word groups.

        Raises:
            FileParseError: If file parsing fails.
        """
        if words_file is None:
            words_file = self.project_root / "config" / "frequency_words.txt"
        else:
            words_file = Path(words_file)

        if not words_file.exists():
            return []

        word_groups = []

        try:
            with open(words_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Use | as separator
                    parts = [p.strip() for p in line.split("|")]
                    if not parts:
                        continue

                    group = {
                        "required": [],
                        "normal": [],
                        "filter_words": []
                    }

                    for part in parts:
                        if not part:
                            continue

                        words = [w.strip() for w in part.split(",")]
                        for word in words:
                            if not word:
                                continue
                            if word.endswith("+"):
                                # Required word
                                group["required"].append(word[:-1])
                            elif word.endswith("!"):
                                # Filter word
                                group["filter_words"].append(word[:-1])
                            else:
                                # Normal word
                                group["normal"].append(word)

                    if group["required"] or group["normal"]:
                        word_groups.append(group)

        except Exception as e:
            raise FileParseError(str(words_file), str(e))

        return word_groups