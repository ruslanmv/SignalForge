# GitHub Pages Setup Guide

This guide explains how to set up GitHub Pages for SignalForge to display English tech news.

## 🚀 Quick Setup

### 1. Enable GitHub Pages

1. Go to your repository settings: `https://github.com/ruslanmv/SignalForge/settings/pages`
2. Under "Source", select **GitHub Actions**
3. Save the settings

### 2. Configure Workflows

The workflow is already set up in `.github/workflows/pages.yml`. It will:
- Run automatically every hour
- Fetch English tech news from major sources
- Generate a professional HTML page
- Deploy to GitHub Pages

### 3. Manual Trigger (Optional)

To manually update the page:
1. Go to Actions tab in your repository
2. Select "Update GitHub Pages with English Tech News"
3. Click "Run workflow"

## 📰 News Sources

The aggregator fetches from these English tech publications:

- **Hacker News** - Tech community news
- **TechCrunch** - Startup and tech news
- **The Verge** - Technology and culture
- **Ars Technica** - In-depth tech analysis
- **Wired** - Technology trends
- **MIT Technology Review** - Emerging technologies
- **Engadget** - Consumer electronics
- **VentureBeat** - Tech business news
- **ZDNet** - Enterprise technology
- **TechRadar** - Tech reviews and news

## 🎨 Features

- ✅ **100% English** - All sources are in English, no Chinese content
- ✅ **Auto-categorization** - News is grouped by AI, Hardware, Cloud, Security, etc.
- ✅ **Professional design** - Modern, responsive layout
- ✅ **Hourly updates** - Fresh news every hour
- ✅ **Mobile-friendly** - Works great on all devices

## 🔧 Customization

### Add More Sources

Edit `fetch_english_news.py` and add to the `NEWS_SOURCES` dictionary:

```python
NEWS_SOURCES = {
    "Your Source": "https://example.com/rss",
    # ...
}
```

### Modify Categories

Edit the `TECH_KEYWORDS` dictionary in `fetch_english_news.py`:

```python
TECH_KEYWORDS = {
    "Your Category": ["keyword1", "keyword2"],
    # ...
}
```

### Change Update Frequency

Edit `.github/workflows/pages.yml`:

```yaml
schedule:
  - cron: "0 */2 * * *"  # Every 2 hours
  - cron: "0 9 * * *"    # Daily at 9 AM
```

## 📊 How It Works

```
┌─────────────────┐
│ GitHub Actions  │  Runs every hour
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│fetch_english_   │  Fetches RSS feeds
│news.py          │  from tech sources
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Categorization  │  Groups by keywords
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate HTML   │  Creates index.html
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GitHub Pages    │  Deploys to web
└─────────────────┘
```

## 🌐 Accessing Your Page

After setup, your page will be available at:

```
https://ruslanmv.github.io/SignalForge/
```

## 🐛 Troubleshooting

### Page not updating?

1. Check Actions tab for workflow runs
2. Ensure GitHub Pages is enabled in settings
3. Verify the workflow has proper permissions

### Getting errors?

1. Check that `requests` is in requirements.txt
2. Ensure Python 3.11+ is being used
3. Review Actions logs for specific errors

### Some sources not loading?

Some RSS feeds may block automated requests or have rate limits. This is normal. The script will gracefully skip failed sources and use the ones that work.

## 📝 License

This project is open source under the LICENSE file in the repository.
