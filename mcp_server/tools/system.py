"""
System Management Tools

Provides functionality for querying system status and triggering crawlers.
"""

from pathlib import Path
from typing import Dict, List, Optional

from ..services.data_service import DataService
from ..utils.validators import validate_platforms
from ..utils.errors import MCPError, CrawlTaskError


class SystemManagementTools:
    """System management tools class"""

    def __init__(self, project_root: str = None):
        """
        Initialize system management tools.

        Args:
            project_root: Project root directory.
        """
        self.data_service = DataService(project_root)
        if project_root:
            self.project_root = Path(project_root)
        else:
            # Get project root directory
            current_file = Path(__file__)
            self.project_root = current_file.parent.parent.parent

    def get_system_status(self) -> Dict:
        """
        Retrieve system running status and health check information.

        Returns:
            System status dictionary.

        Example:
            >>> tools = SystemManagementTools()
            >>> result = tools.get_system_status()
            >>> print(result['system']['version'])
        """
        try:
            # Get system status
            status = self.data_service.get_system_status()

            return {
                **status,
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

    def trigger_crawl(
        self, 
        platforms: Optional[List[str]] = None, 
        save_to_local: bool = False, 
        include_url: bool = False
    ) -> Dict:
        """
        Manually trigger a temporary crawl task (optional persistence).

        Args:
            platforms: List of specific platforms. Crawls all if empty.
            save_to_local: Whether to save to local 'output' directory. Default is False.
            include_url: Whether to include URL links. Default is False (to save tokens).

        Returns:
            Crawl result dictionary, containing news data and save paths (if saved).

        Example:
            >>> tools = SystemManagementTools()
            >>> # Temporary crawl, do not save
            >>> result = tools.trigger_crawl(platforms=['zhihu', 'weibo'])
            >>> print(result['data'])
            >>> # Crawl and save to local
            >>> result = tools.trigger_crawl(platforms=['zhihu'], save_to_local=True)
            >>> print(result['saved_files'])
        """
        try:
            import json
            import time
            import random
            import requests
            from datetime import datetime
            import pytz
            import yaml

            # Parameter validation
            platforms = validate_platforms(platforms)

            # Load configuration file
            config_path = self.project_root / "config" / "config.yaml"
            if not config_path.exists():
                raise CrawlTaskError(
                    "Configuration file not found",
                    suggestion=f"Please ensure the config file exists: {config_path}"
                )

            # Read configuration
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # Get platform configuration
            all_platforms = config_data.get("platforms", [])
            if not all_platforms:
                raise CrawlTaskError(
                    "No platform configuration found",
                    suggestion="Please check the 'platforms' section in config/config.yaml"
                )

            # Filter platforms
            if platforms:
                target_platforms = [p for p in all_platforms if p["id"] in platforms]
                if not target_platforms:
                    raise CrawlTaskError(
                        f"Specified platforms do not exist: {platforms}",
                        suggestion=f"Available platforms: {[p['id'] for p in all_platforms]}"
                    )
            else:
                target_platforms = all_platforms

            # Get request interval
            request_interval = config_data.get("crawler", {}).get("request_interval", 100)

            # Build platform ID list
            ids = []
            for platform in target_platforms:
                if "name" in platform:
                    ids.append((platform["id"], platform["name"]))
                else:
                    ids.append(platform["id"])

            print(f"Starting temporary crawl. Platforms: {[p.get('name', p['id']) for p in target_platforms]}")

            # Crawl data
            results = {}
            id_to_name = {}
            failed_ids = []

            for i, id_info in enumerate(ids):
                if isinstance(id_info, tuple):
                    id_value, name = id_info
                else:
                    id_value = id_info
                    name = id_value

                id_to_name[id_value] = name

                # Build request URL
                url = f"https://newsnow.busiyi.world/api/s?id={id_value}&latest"

                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Connection": "keep-alive",
                    "Cache-Control": "no-cache",
                }

                # Retry mechanism
                max_retries = 2
                retries = 0
                success = False

                while retries <= max_retries and not success:
                    try:
                        response = requests.get(url, headers=headers, timeout=10)
                        response.raise_for_status()

                        data_text = response.text
                        data_json = json.loads(data_text)

                        status = data_json.get("status", "unknown")
                        if status not in ["success", "cache"]:
                            raise ValueError(f"Abnormal response status: {status}")

                        status_info = "Latest Data" if status == "success" else "Cached Data"
                        print(f"Successfully retrieved {id_value} ({status_info})")

                        # Parse data
                        results[id_value] = {}
                        for index, item in enumerate(data_json.get("items", []), 1):
                            title = item["title"]
                            url_link = item.get("url", "")
                            mobile_url = item.get("mobileUrl", "")

                            if title in results[id_value]:
                                results[id_value][title]["ranks"].append(index)
                            else:
                                results[id_value][title] = {
                                    "ranks": [index],
                                    "url": url_link,
                                    "mobileUrl": mobile_url,
                                }

                        success = True

                    except Exception as e:
                        retries += 1
                        if retries <= max_retries:
                            wait_time = random.uniform(3, 5)
                            print(f"Request to {id_value} failed: {e}. Retrying in {wait_time:.2f} seconds...")
                            time.sleep(wait_time)
                        else:
                            print(f"Request to {id_value} failed: {e}")
                            failed_ids.append(id_value)

                # Request interval
                if i < len(ids) - 1:
                    actual_interval = request_interval + random.randint(-10, 20)
                    actual_interval = max(50, actual_interval)
                    time.sleep(actual_interval / 1000)

            # Format return data
            news_data = []
            for platform_id, titles_data in results.items():
                platform_name = id_to_name.get(platform_id, platform_id)
                for title, info in titles_data.items():
                    news_item = {
                        "platform_id": platform_id,
                        "platform_name": platform_name,
                        "title": title,
                        "ranks": info["ranks"]
                    }

                    # Conditionally add URL fields
                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobile_url"] = info.get("mobileUrl", "")

                    news_data.append(news_item)

            # Get Beijing time (or local server time)
            beijing_tz = pytz.timezone("Asia/Shanghai")
            now = datetime.now(beijing_tz)

            # Build result
            result = {
                "success": True,
                "task_id": f"crawl_{int(time.time())}",
                "status": "completed",
                "crawl_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "platforms": list(results.keys()),
                "total_news": len(news_data),
                "failed_platforms": failed_ids,
                "data": news_data,
                "saved_to_local": save_to_local
            }

            # Call save logic if persistence is required
            if save_to_local:
                try:
                    import re

                    # Helper function: Clean title
                    def clean_title(title: str) -> str:
                        """Clean special characters in title"""
                        if not isinstance(title, str):
                            title = str(title)
                        cleaned_title = title.replace("\n", " ").replace("\r", " ")
                        cleaned_title = re.sub(r"\s+", " ", cleaned_title)
                        cleaned_title = cleaned_title.strip()
                        return cleaned_title

                    # Helper function: Ensure directory exists
                    def ensure_directory_exists(directory: str):
                        """Ensure directory exists"""
                        Path(directory).mkdir(parents=True, exist_ok=True)

                    # Format date and time (Note: keeping Chinese format for folder structure compatibility)
                    date_folder = now.strftime("%Y年%m月%d日")
                    time_filename = now.strftime("%H时%M分")

                    # Create TXT file path
                    txt_dir = self.project_root / "output" / date_folder / "txt"
                    ensure_directory_exists(str(txt_dir))
                    txt_file_path = txt_dir / f"{time_filename}.txt"

                    # Create HTML file path
                    html_dir = self.project_root / "output" / date_folder / "html"
                    ensure_directory_exists(str(html_dir))
                    html_file_path = html_dir / f"{time_filename}.html"

                    # Save TXT file (following main.py format)
                    with open(txt_file_path, "w", encoding="utf-8") as f:
                        for id_value, title_data in results.items():
                            # id | name or id
                            name = id_to_name.get(id_value)
                            if name and name != id_value:
                                f.write(f"{id_value} | {name}\n")
                            else:
                                f.write(f"{id_value}\n")

                            # Sort titles by rank
                            sorted_titles = []
                            for title, info in title_data.items():
                                cleaned = clean_title(title)
                                if isinstance(info, dict):
                                    ranks = info.get("ranks", [])
                                    url = info.get("url", "")
                                    mobile_url = info.get("mobileUrl", "")
                                else:
                                    ranks = info if isinstance(info, list) else []
                                    url = ""
                                    mobile_url = ""

                                rank = ranks[0] if ranks else 1
                                sorted_titles.append((rank, cleaned, url, mobile_url))

                            sorted_titles.sort(key=lambda x: x[0])

                            for rank, cleaned, url, mobile_url in sorted_titles:
                                line = f"{rank}. {cleaned}"
                                if url:
                                    line += f" [URL:{url}]"
                                if mobile_url:
                                    line += f" [MOBILE:{mobile_url}]"
                                f.write(line + "\n")

                            f.write("\n")

                        if failed_ids:
                            f.write("==== Failed IDs ====\n")
                            for id_value in failed_ids:
                                f.write(f"{id_value}\n")

                    # Save HTML file (simplified version)
                    html_content = self._generate_simple_html(results, id_to_name, failed_ids, now)
                    with open(html_file_path, "w", encoding="utf-8") as f:
                        f.write(html_content)

                    print(f"Data saved to:")
                    print(f"  TXT: {txt_file_path}")
                    print(f"  HTML: {html_file_path}")

                    result["saved_files"] = {
                        "txt": str(txt_file_path),
                        "html": str(html_file_path)
                    }
                    result["note"] = "Data persisted to output folder"

                except Exception as e:
                    print(f"Failed to save file: {e}")
                    result["save_error"] = str(e)
                    result["note"] = "Crawl successful but save failed. Data is in memory only."
            else:
                result["note"] = "Temporary crawl result, not persisted to output folder."

            return result

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e),
                    "traceback": traceback.format_exc()
                }
            }

    def _generate_simple_html(self, results: Dict, id_to_name: Dict, failed_ids: List, now) -> str:
        """Generate simplified HTML report"""
        html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Crawl Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }
        .platform { margin-bottom: 30px; }
        .platform-name { background: #4CAF50; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
        .news-item { padding: 8px; border-bottom: 1px solid #eee; }
        .rank { color: #666; font-weight: bold; margin-right: 10px; }
        .title { color: #333; }
        .link { color: #1976D2; text-decoration: none; margin-left: 10px; font-size: 0.9em; }
        .link:hover { text-decoration: underline; }
        .failed { background: #ffebee; padding: 10px; border-radius: 5px; margin-top: 20px; }
        .failed h3 { color: #c62828; margin-top: 0; }
        .timestamp { color: #666; font-size: 0.9em; text-align: right; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>MCP Crawl Results</h1>
"""

        # Add timestamp
        html += f'        <p class="timestamp">Crawl Time: {now.strftime("%Y-%m-%d %H:%M:%S")}</p>\n\n'

        # Iterate through each platform
        for platform_id, titles_data in results.items():
            platform_name = id_to_name.get(platform_id, platform_id)
            html += f'        <div class="platform">\n'
            html += f'            <div class="platform-name">{platform_name}</div>\n'

            # Sort titles
            sorted_items = []
            for title, info in titles_data.items():
                ranks = info.get("ranks", [])
                url = info.get("url", "")
                mobile_url = info.get("mobileUrl", "")
                rank = ranks[0] if ranks else 999
                sorted_items.append((rank, title, url, mobile_url))

            sorted_items.sort(key=lambda x: x[0])

            # Display news
            for rank, title, url, mobile_url in sorted_items:
                html += f'            <div class="news-item">\n'
                html += f'                <span class="rank">{rank}.</span>\n'
                html += f'                <span class="title">{self._html_escape(title)}</span>\n'
                if url:
                    html += f'                <a class="link" href="{self._html_escape(url)}" target="_blank">Link</a>\n'
                if mobile_url and mobile_url != url:
                    html += f'                <a class="link" href="{self._html_escape(mobile_url)}" target="_blank">Mobile</a>\n'
                html += '            </div>\n'

            html += '        </div>\n\n'

        # Failed platforms
        if failed_ids:
            html += '        <div class="failed">\n'
            html += '            <h3>Failed Platforms</h3>\n'
            html += '            <ul>\n'
            for platform_id in failed_ids:
                html += f'                <li>{self._html_escape(platform_id)}</li>\n'
            html += '            </ul>\n'
            html += '        </div>\n'

        html += """    </div>
</body>
</html>"""

        return html

    def _html_escape(self, text: str) -> str:
        """HTML Escape"""
        if not isinstance(text, str):
            text = str(text)
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#x27;")
        )