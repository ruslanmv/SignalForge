# English News Sources for SignalForge

This document explains how to manage and health-check the English tech news sources.

## Files

- **`sources.json`** - Configuration file containing all news sources
- **`check_news_sources.py`** - Health check script to verify RSS feeds
- **`fetch_english_news.py`** - Main script that fetches and generates the news page

## Health Check Script

### Usage

Run the health check to verify all news sources are working:

```bash
python3 check_news_sources.py
```

This will:
- ✅ Test each RSS feed for connectivity
- ✅ Verify feeds return valid content
- ✅ Check that articles have titles and links
- ✅ Report response times and item counts
- ✅ Save working sources to `sources.json`

### Output Example

```
🏥 News Sources Health Check
================================================================================

Checking 30 news sources...

[1/30] The Register              ✓ OK (0.29s, 50 items)
[2/30] Hacker News Best          ✗ HTTP 503
[3/30] Lobsters                  ✓ OK (0.45s, 25 items)
...

Summary
================================================================================

Total Sources:   30
Working:         25 (83.3%)
Broken:          5 (16.7%)
```

## Managing Sources

### Adding a New Source

1. Edit `sources.json` and add your RSS feed:

```json
{
  "sources": {
    "Your Source Name": "https://example.com/feed.xml"
  }
}
```

2. Run the health check to verify it works:

```bash
python3 check_news_sources.py
```

3. If it passes, commit the changes:

```bash
git add sources.json
git commit -m "Add new news source: Your Source Name"
git push
```

### Removing a Broken Source

1. Run health check to identify broken sources:

```bash
python3 check_news_sources.py
```

2. Remove the broken source from `sources.json`

3. Commit the changes

## Manual Testing

### Test News Fetching Locally

```bash
python3 fetch_english_news.py
```

This will generate `index.html` with the latest tech news.

### View Results

Open `index.html` in your browser to see the formatted news feed.

## GitHub Actions Workflow

The workflow runs automatically:
- **Every hour** via cron schedule
- **On push** to main/master branch
- **Manually** via workflow_dispatch

### Manual Trigger

1. Go to GitHub repository
2. Click "Actions" tab
3. Select "Update GitHub Pages with English Tech News"
4. Click "Run workflow"
5. Select branch and click "Run workflow"

## Troubleshooting

### All Sources Showing as Broken

This may indicate:
- Network connectivity issues
- Rate limiting from RSS providers
- IP blocking (some feeds block datacenter IPs)

**Solution**: Run the health check from a different network or use the feeds that are consistently working.

### Sources Work Locally But Fail in GitHub Actions

Some RSS feeds block automated requests. Solutions:
- Use alternative feeds from the same source
- Find mirrors or aggregators
- Contact the source for API access

### XML Parse Errors

Some feeds may have malformed XML. The health check will report these as "XML Parse Error".

**Solution**: Try alternative feeds or contact the publisher.

## Current Working Sources

The following sources have been tested and generally work well:

- **The Register** - Reliable tech news
- **Hacker News** (via hnrss.org) - Community tech discussions
- **Lobsters** - Tech community news
- **Phoronix** - Linux and open source hardware
- **Bleeping Computer** - Security and tech news
- **Android Authority** - Mobile tech news
- **9to5Mac/9to5Google** - Apple and Google news

## Notes

- Some sources may be intermittently unavailable (503 errors)
- Cloudflare-protected sites may block automated requests (403 errors)
- Reddit feeds may require special handling for API access
- Always verify sources manually before adding to production

## Support

For issues or questions:
- Create an issue in the GitHub repository
- Include the output of `check_news_sources.py`
- Provide the specific source that's having issues
