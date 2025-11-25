#!/usr/bin/env python3
"""
News Sources Health Check Script
Verifies if RSS feeds are alive and returning valid data
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import requests
import time

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def check_source_health(source_name: str, feed_url: str, timeout: int = 15) -> Tuple[bool, str, int]:
    """
    Check if a news source is healthy and returning data

    Returns:
        (is_healthy, status_message, item_count)
    """
    try:
        # Fetch RSS feed
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        start_time = time.time()
        response = requests.get(feed_url, headers=headers, timeout=timeout)
        response_time = time.time() - start_time

        # Check HTTP status
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}", 0

        # Parse XML
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            return False, f"XML Parse Error: {str(e)[:50]}", 0

        # Check for items (RSS or Atom)
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        item_count = len(items)

        if item_count == 0:
            return False, "No items found in feed", 0

        # Check if first item has required fields
        first_item = items[0]

        # Find title
        title_elem = first_item.find('title') or first_item.find('{http://www.w3.org/2005/Atom}title')
        title_text = ''
        if title_elem is not None and title_elem.text:
            title_text = title_elem.text.strip()

        if not title_text:
            return False, "Items missing title", item_count

        # Find link
        link_elem = first_item.find('link') or first_item.find('{http://www.w3.org/2005/Atom}link')
        if link_elem is None:
            return False, "Items missing link", item_count

        # All checks passed
        status_msg = f"OK ({response_time:.2f}s, {item_count} items)"
        return True, status_msg, item_count

    except requests.exceptions.Timeout:
        return False, f"Timeout (>{timeout}s)", 0
    except requests.exceptions.ConnectionError:
        return False, "Connection Error", 0
    except requests.exceptions.TooManyRedirects:
        return False, "Too Many Redirects", 0
    except requests.exceptions.RequestException as e:
        return False, f"Request Error: {str(e)[:50]}", 0
    except Exception as e:
        return False, f"Unknown Error: {str(e)[:50]}", 0


def load_sources(sources_file: str = "sources.json") -> Dict[str, str]:
    """Load sources from JSON file"""
    try:
        with open(sources_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('sources', {})
    except FileNotFoundError:
        print(f"{YELLOW}Warning: {sources_file} not found, using default sources{RESET}")
        # Default fallback sources
        return {
            "Hacker News": "https://hnrss.org/frontpage",
            "TechCrunch": "https://techcrunch.com/feed/",
            "The Verge": "https://www.theverge.com/rss/index.xml",
            "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
            "Wired": "https://www.wired.com/feed/rss",
            "MIT Tech Review": "https://www.technologyreview.com/feed/",
            "Engadget": "https://www.engadget.com/rss.xml",
            "VentureBeat": "https://venturebeat.com/feed/",
            "ZDNet": "https://www.zdnet.com/news/rss.xml",
            "TechRadar": "https://www.techradar.com/rss"
        }
    except json.JSONDecodeError as e:
        print(f"{RED}Error: Invalid JSON in {sources_file}: {e}{RESET}")
        return {}


def save_working_sources(working_sources: Dict[str, str], output_file: str = "sources.json"):
    """Save working sources to JSON file"""
    data = {
        "last_checked": datetime.now(timezone.utc).isoformat(),
        "sources": working_sources,
        "total_sources": len(working_sources)
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n{GREEN}✓ Saved {len(working_sources)} working sources to {output_file}{RESET}")


def main():
    """Main health check function"""
    print(f"{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}🏥 News Sources Health Check{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

    # Load sources
    sources = load_sources()

    if not sources:
        print(f"{RED}Error: No sources to check{RESET}")
        return

    print(f"Checking {len(sources)} news sources...\n")

    # Check each source
    results = []
    working_sources = {}
    broken_sources = {}

    for i, (source_name, feed_url) in enumerate(sources.items(), 1):
        print(f"[{i}/{len(sources)}] {source_name:25s} ", end='', flush=True)

        is_healthy, status_msg, item_count = check_source_health(source_name, feed_url)

        results.append({
            'name': source_name,
            'url': feed_url,
            'healthy': is_healthy,
            'status': status_msg,
            'items': item_count
        })

        if is_healthy:
            print(f"{GREEN}✓ {status_msg}{RESET}")
            working_sources[source_name] = feed_url
        else:
            print(f"{RED}✗ {status_msg}{RESET}")
            broken_sources[source_name] = feed_url

    # Print summary
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Summary{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

    total = len(sources)
    working = len(working_sources)
    broken = len(broken_sources)

    print(f"Total Sources:   {total}")
    print(f"{GREEN}Working:         {working} ({working/total*100:.1f}%){RESET}")
    print(f"{RED}Broken:          {broken} ({broken/total*100:.1f}%){RESET}\n")

    # Show working sources
    if working_sources:
        print(f"{GREEN}Working Sources:{RESET}")
        for name in working_sources:
            item_count = next(r['items'] for r in results if r['name'] == name)
            print(f"  ✓ {name:25s} ({item_count} articles)")

    # Show broken sources
    if broken_sources:
        print(f"\n{RED}Broken Sources:{RESET}")
        for name in broken_sources:
            status = next(r['status'] for r in results if r['name'] == name)
            print(f"  ✗ {name:25s} - {status}")

    # Save working sources
    if working_sources:
        save_working_sources(working_sources)
    else:
        print(f"\n{RED}Warning: No working sources found!{RESET}")

    # Generate detailed report
    print(f"\n{BLUE}Detailed Report{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")

    for result in results:
        status_icon = f"{GREEN}✓{RESET}" if result['healthy'] else f"{RED}✗{RESET}"
        print(f"{status_icon} {result['name']}")
        print(f"  URL: {result['url']}")
        print(f"  Status: {result['status']}")
        if result['items'] > 0:
            print(f"  Items: {result['items']}")
        print()


if __name__ == "__main__":
    main()
