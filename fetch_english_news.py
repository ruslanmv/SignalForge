#!/usr/bin/env python3
"""
English Tech News Aggregator for SignalForge
Fetches news from major English tech publications
"""

import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List, Dict
import requests
from collections import defaultdict
import re
from email.utils import parsedate_to_datetime

# English Tech News Sources (RSS Feeds)
NEWS_SOURCES = {
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

# Tech keywords to categorize and filter news
TECH_KEYWORDS = {
    "AI & Machine Learning": [
        "AI", "Artificial Intelligence", "Machine Learning", "ChatGPT", "GPT-4",
        "Claude", "Anthropic", "Gemini", "DeepMind", "Sora", "Neural Network",
        "LLM", "OpenAI", "Deep Learning", "GenAI", "Generative AI"
    ],
    "Semiconductors & Hardware": [
        "Chip", "Semiconductor", "Lithography", "GPU", "CPU", "NVIDIA",
        "AMD", "Intel", "TSMC", "Processor", "Silicon"
    ],
    "Cloud & Enterprise": [
        "Cloud", "AWS", "Azure", "Google Cloud", "SaaS", "Enterprise",
        "Data Center", "Serverless", "Kubernetes"
    ],
    "Cybersecurity": [
        "Security", "Cyber", "Breach", "Hack", "Vulnerability", "Encryption",
        "Privacy", "Ransomware", "Zero-day"
    ],
    "Software Development": [
        "Programming", "Developer", "GitHub", "Open Source", "API",
        "Framework", "Python", "JavaScript", "Rust"
    ],
    "Mobile & Devices": [
        "iPhone", "Android", "Smartphone", "Mobile", "Tablet", "Apple",
        "Samsung", "Google Pixel"
    ],
    "Startups & Funding": [
        "Startup", "Funding", "VC", "Venture Capital", "IPO", "Acquisition",
        "Series A", "Series B", "Investment"
    ]
}


def fetch_news_from_source(source_name: str, feed_url: str, max_items: int = 10) -> List[Dict]:
    """Fetch news from a single RSS feed source"""
    news_items = []

    try:
        print(f"Fetching from {source_name}...")

        # Fetch RSS feed
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(feed_url, headers=headers, timeout=15)
        response.raise_for_status()

        # Parse XML
        root = ET.fromstring(response.content)

        # Handle both RSS and Atom feeds
        # RSS uses <item>, Atom uses <entry>
        items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')

        for item in items[:max_items]:
            # Get title
            title_elem = item.find('title') or item.find('{http://www.w3.org/2005/Atom}title')
            title = title_elem.text if title_elem is not None else ''

            # Get link
            link_elem = item.find('link') or item.find('{http://www.w3.org/2005/Atom}link')
            if link_elem is not None:
                link = link_elem.text if link_elem.text else link_elem.get('href', '')
            else:
                link = ''

            # Get publication date
            pub_date = None
            for date_tag in ['pubDate', 'published', 'updated', '{http://www.w3.org/2005/Atom}published', '{http://www.w3.org/2005/Atom}updated']:
                date_elem = item.find(date_tag)
                if date_elem is not None and date_elem.text:
                    try:
                        pub_date = parsedate_to_datetime(date_elem.text)
                        break
                    except:
                        try:
                            # Try ISO format
                            pub_date = datetime.fromisoformat(date_elem.text.replace('Z', '+00:00'))
                            break
                        except:
                            pass

            if pub_date is None:
                pub_date = datetime.now(timezone.utc)
            elif pub_date.tzinfo is None:
                pub_date = pub_date.replace(tzinfo=timezone.utc)

            news_items.append({
                'source': source_name,
                'title': title.strip(),
                'link': link,
                'published': pub_date,
                'timestamp': pub_date.timestamp()
            })

        print(f"  ✓ Found {len(news_items)} items from {source_name}")

    except Exception as e:
        print(f"  ✗ Error fetching from {source_name}: {str(e)}")

    return news_items


def categorize_news(news_items: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize news items by keywords"""
    categorized = defaultdict(list)
    uncategorized = []

    for item in news_items:
        title_lower = item['title'].lower()
        matched = False

        for category, keywords in TECH_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    categorized[category].append(item)
                    matched = True
                    break
            if matched:
                break

        if not matched:
            uncategorized.append(item)

    # Add uncategorized to "General Tech News"
    if uncategorized:
        categorized["General Tech News"] = uncategorized

    return dict(categorized)


def generate_html(categorized_news: Dict[str, List[Dict]]) -> str:
    """Generate professional HTML from categorized news"""

    # Count total news
    total_news = sum(len(items) for items in categorized_news.values())
    num_categories = len(categorized_news)

    # Get current time
    now = datetime.now(timezone.utc)
    generation_time = now.strftime("%m-%d %H:%M UTC")

    # Start HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="SignalForge - Real-time English Tech News Aggregator">
    <title>SignalForge - Tech News Analysis</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js" integrity="sha512-BNaRQnYJYiPSqHHDb58B0yaPfCu+Wgds8Gp/gU33kqBtgNS4tSPHuGibyoeqMV/TJlSKda6FXzoEyYGjTe+vXA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
    <style>
        * {{ box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            line-height: 1.6;
            min-height: 100vh;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}

        .header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
            padding: 40px 32px;
            position: relative;
        }}

        .header-title {{
            font-size: 32px;
            font-weight: 800;
            margin: 0 0 24px 0;
            letter-spacing: -0.5px;
        }}

        .header-subtitle {{
            font-size: 16px;
            opacity: 0.9;
            margin-bottom: 24px;
            font-weight: 400;
        }}

        .header-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-top: 20px;
        }}

        .stat-card {{
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            padding: 16px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        .stat-label {{
            font-size: 12px;
            opacity: 0.85;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .stat-value {{
            font-size: 28px;
            font-weight: 700;
        }}

        .content {{
            padding: 32px;
        }}

        .category-section {{
            margin-bottom: 48px;
        }}

        .category-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 3px solid #e5e7eb;
        }}

        .category-title {{
            font-size: 22px;
            font-weight: 700;
            color: #1e293b;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .category-icon {{
            font-size: 24px;
        }}

        .category-count {{
            background: #3b82f6;
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 14px;
            font-weight: 600;
        }}

        .news-grid {{
            display: grid;
            gap: 16px;
        }}

        .news-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .news-card::before {{
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .news-card:hover {{
            transform: translateX(4px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.1);
            border-color: #3b82f6;
        }}

        .news-card:hover::before {{
            opacity: 1;
        }}

        .news-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 8px;
        }}

        .news-source {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: white;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            color: #3b82f6;
            border: 1px solid #dbeafe;
        }}

        .news-time {{
            color: #64748b;
            font-size: 13px;
        }}

        .news-title {{
            font-size: 16px;
            line-height: 1.5;
            margin: 0;
        }}

        .news-link {{
            color: #1e293b;
            text-decoration: none;
            font-weight: 500;
            transition: color 0.2s ease;
        }}

        .news-link:hover {{
            color: #3b82f6;
            text-decoration: underline;
        }}

        .footer {{
            background: #f1f5f9;
            padding: 32px;
            text-align: center;
            border-top: 1px solid #e2e8f0;
        }}

        .footer-content {{
            font-size: 14px;
            color: #64748b;
            line-height: 1.8;
        }}

        .footer-link {{
            color: #3b82f6;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.2s ease;
        }}

        .footer-link:hover {{
            color: #1e40af;
            text-decoration: underline;
        }}

        .badge {{
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        @media (max-width: 768px) {{
            body {{ padding: 12px; }}
            .header {{ padding: 32px 24px; }}
            .content {{ padding: 24px 20px; }}
            .header-title {{ font-size: 26px; }}
            .category-title {{ font-size: 18px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-title">🚀 SignalForge Tech News</div>
            <div class="header-subtitle">Real-time aggregation from leading English tech publications</div>

            <div class="header-stats">
                <div class="stat-card">
                    <div class="stat-label">Total Articles</div>
                    <div class="stat-value">{total_news}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Categories</div>
                    <div class="stat-value">{num_categories}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Last Updated</div>
                    <div class="stat-value" style="font-size: 18px;">{generation_time}</div>
                </div>
            </div>
        </div>

        <div class="content">
"""

    # Category icons
    category_icons = {
        "AI & Machine Learning": "🤖",
        "Semiconductors & Hardware": "💻",
        "Cloud & Enterprise": "☁️",
        "Cybersecurity": "🔒",
        "Software Development": "⚡",
        "Mobile & Devices": "📱",
        "Startups & Funding": "💰",
        "General Tech News": "📰"
    }

    # Sort categories by number of items (most items first)
    sorted_categories = sorted(categorized_news.items(), key=lambda x: len(x[1]), reverse=True)

    # Generate each category section
    for idx, (category, news_items) in enumerate(sorted_categories):
        icon = category_icons.get(category, "📌")

        html += f"""
            <div class="category-section">
                <div class="category-header">
                    <div class="category-title">
                        <span class="category-icon">{icon}</span>
                        {category}
                    </div>
                    <div class="category-count">{len(news_items)} articles</div>
                </div>

                <div class="news-grid">
"""

        # Sort news items by timestamp (newest first)
        sorted_news = sorted(news_items, key=lambda x: x['timestamp'], reverse=True)

        # Add each news item
        for news_idx, item in enumerate(sorted_news[:15]):  # Limit to 15 items per category
            time_str = item['published'].strftime("%b %d, %H:%M UTC")

            html += f"""
                    <div class="news-card">
                        <div class="news-header">
                            <span class="news-source">📡 {item['source']}</span>
                            <span class="news-time">🕐 {time_str}</span>
                        </div>
                        <div class="news-title">
                            <a href="{item['link']}" target="_blank" rel="noopener noreferrer" class="news-link">
                                {item['title']}
                            </a>
                        </div>
                    </div>
"""

        html += """
                </div>
            </div>
"""

    # Close HTML
    html += f"""
        </div>

        <div class="footer">
            <div class="footer-content">
                <strong>Powered by SignalForge</strong> 🔥<br>
                An open-source tech news aggregator · Auto-updated every hour<br>
                <a href="https://github.com/ruslanmv/SignalForge" target="_blank" rel="noopener noreferrer" class="footer-link">
                    View on GitHub ⭐
                </a>
            </div>
        </div>
    </div>
</body>
</html>
"""

    return html


def main():
    """Main function to fetch and generate news"""
    print("🚀 SignalForge - Fetching English Tech News")
    print("=" * 60)

    all_news = []

    # Fetch from all sources
    for source_name, feed_url in NEWS_SOURCES.items():
        news_items = fetch_news_from_source(source_name, feed_url)
        all_news.extend(news_items)

    print(f"\n✓ Total news items fetched: {len(all_news)}")

    # Categorize news
    print("\n📊 Categorizing news...")
    categorized = categorize_news(all_news)

    for category, items in categorized.items():
        print(f"  • {category}: {len(items)} items")

    # Generate HTML
    print("\n📝 Generating HTML...")
    html_content = generate_html(categorized)

    # Save to index.html
    output_file = "index.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✅ Successfully generated {output_file}")
    print(f"   Total articles: {len(all_news)}")
    print(f"   Categories: {len(categorized)}")


if __name__ == "__main__":
    main()
