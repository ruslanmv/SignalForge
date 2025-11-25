#!/usr/bin/env python3
"""
RSS News Source Health Checker for SignalForge
Verifies if news sources are alive and returning valid content
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import requests
from email.utils import parsedate_to_datetime
import sys

# ANSI color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def check_rss_source(source_name: str, feed_url: str, timeout: int = 15) -> Tuple[bool, Dict]:
    """
    Check if an RSS feed source is healthy and returning content

    Returns:
        (is_healthy, details_dict)
    """
    details = {
        "source": source_name,
        "url": feed_url,
        "status": "unknown",
        "items_found": 0,
        "error": None,
        "response_time": None,
        "last_item_date": None
    }

    try:
        # Fetch RSS feed with timeout
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        start_time = datetime.now()
        response = requests.get(feed_url, headers=headers, timeout=timeout)
        response_time = (datetime.now() - start_time).total_seconds()
        details["response_time"] = round(response_time, 2)

        # Check HTTP status
        if response.status_code != 200:
            details["status"] = "error"
            details["error"] = f"HTTP {response.status_code}"
            return False, details

        # Try to parse XML
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            details["status"] = "error"
            details["error"] = f"Invalid XML: {str(e)[:50]}"
            return False, details

        # Find items (RSS or Atom format)
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
        details["items_found"] = len(items)

        if len(items) == 0:
            details["status"] = "warning"
            details["error"] = "No items found in feed"
            return False, details

        # Get the date of the most recent item
        first_item = items[0]
        for date_tag in ['pubDate', 'published', 'updated',
                        '{http://www.w3.org/2005/Atom}published',
                        '{http://www.w3.org/2005/Atom}updated']:
            date_elem = first_item.find(date_tag)
            if date_elem is not None and date_elem.text:
                try:
                    pub_date = parsedate_to_datetime(date_elem.text)
                    details["last_item_date"] = pub_date.strftime("%Y-%m-%d %H:%M UTC")
                    break
                except:
                    try:
                        pub_date = datetime.fromisoformat(date_elem.text.replace('Z', '+00:00'))
                        details["last_item_date"] = pub_date.strftime("%Y-%m-%d %H:%M UTC")
                        break
                    except:
                        pass

        details["status"] = "healthy"
        return True, details

    except requests.Timeout:
        details["status"] = "error"
        details["error"] = "Request timeout"
        return False, details
    except requests.ConnectionError:
        details["status"] = "error"
        details["error"] = "Connection error"
        return False, details
    except Exception as e:
        details["status"] = "error"
        details["error"] = str(e)[:100]
        return False, details


def load_sources_from_file(filepath: str = "sources.json") -> Dict[str, str]:
    """Load news sources from JSON file"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data.get("sources", {})
    except FileNotFoundError:
        print(f"{YELLOW}⚠️  sources.json not found, using default sources{RESET}")
        # Default sources if file doesn't exist
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


def save_health_report(results: List[Dict], output_file: str = "health_report.json"):
    """Save health check results to JSON file"""
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "total_sources": len(results),
        "healthy_sources": sum(1 for r in results if r["status"] == "healthy"),
        "failed_sources": sum(1 for r in results if r["status"] == "error"),
        "sources": results
    }

    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    return output_file


def main():
    """Main function to check all news sources"""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}🔍 SignalForge RSS Source Health Checker{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")

    # Load sources
    sources = load_sources_from_file()
    print(f"📋 Checking {len(sources)} news sources...\n")

    results = []
    healthy_count = 0
    failed_count = 0

    # Check each source
    for idx, (source_name, feed_url) in enumerate(sources.items(), 1):
        print(f"{BOLD}[{idx}/{len(sources)}] Checking {source_name}...{RESET}")
        is_healthy, details = check_rss_source(source_name, feed_url)
        results.append(details)

        if is_healthy:
            healthy_count += 1
            print(f"  {GREEN}✓ HEALTHY{RESET}")
            print(f"    Items: {details['items_found']}")
            print(f"    Response time: {details['response_time']}s")
            if details['last_item_date']:
                print(f"    Latest article: {details['last_item_date']}")
        else:
            failed_count += 1
            status_color = YELLOW if details['status'] == 'warning' else RED
            print(f"  {status_color}✗ {details['status'].upper()}{RESET}")
            print(f"    Error: {details['error']}")
            if details['response_time']:
                print(f"    Response time: {details['response_time']}s")
        print()

    # Summary
    print(f"{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}📊 Health Check Summary{RESET}\n")
    print(f"  Total sources checked: {len(sources)}")
    print(f"  {GREEN}✓ Healthy sources: {healthy_count}{RESET}")
    print(f"  {RED}✗ Failed sources: {failed_count}{RESET}")
    print(f"  Success rate: {(healthy_count/len(sources)*100):.1f}%\n")

    # Save report
    report_file = save_health_report(results)
    print(f"💾 Detailed report saved to: {report_file}\n")

    # List working sources
    if healthy_count > 0:
        print(f"{BOLD}{GREEN}Working Sources:{RESET}")
        for result in results:
            if result['status'] == 'healthy':
                print(f"  ✓ {result['source']}")
        print()

    # List failed sources
    if failed_count > 0:
        print(f"{BOLD}{RED}Failed Sources:{RESET}")
        for result in results:
            if result['status'] != 'healthy':
                print(f"  ✗ {result['source']}: {result['error']}")
        print()

    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")

    # Exit with error code if any sources failed
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
