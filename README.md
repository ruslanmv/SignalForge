# SignalForge

<div align="center">

**AI-Powered Trending News Intelligence Platform**

*Filtering signal from noise - monitor what matters to you*

[![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/version-v2.0.0-blue.svg)](#)
[![MCP](https://img.shields.io/badge/MCP-v2.0.0-green.svg)](#)

[![Docker](https://img.shields.io/badge/Docker-Deployment-2496ED?style=flat-square&logo=docker&logoColor=white)](#docker-deployment)
[![MCP Support](https://img.shields.io/badge/MCP-AI_Analysis-FF6B6B?style=flat-square&logo=ai&logoColor=white)](https://modelcontextprotocol.io/)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [MCP Server](#mcp-server)
- [Deployment Options](#deployment-options)
- [Notification Channels](#notification-channels)
- [License](#license)

---

## 🎯 Overview

**SignalForge** is an intelligent news aggregation and monitoring platform that helps you stay informed about topics that matter to you. Instead of drowning in information overload, SignalForge filters trending news from multiple platforms and delivers only what's relevant based on your custom keywords.

### Why SignalForge?

- **🎯 Focused Monitoring**: Define your own keywords and get notifications only for relevant news
- **📊 Multi-Platform Aggregation**: Collects trending topics from 10+ news platforms
- **🤖 AI-Powered Analysis**: Built-in MCP server for AI-assisted news analysis
- **🔔 Smart Notifications**: Multiple notification channels (Telegram, Email, Feishu, DingTalk, etc.)
- **⚡ Lightweight & Fast**: Designed for easy deployment and minimal resource usage

---

## ✨ Key Features

### 📰 News Aggregation
- **Multi-Platform Support**: Aggregates from 10+ popular news platforms
- **Smart Filtering**: Filter news by custom keywords defined in `config/frequency_words.txt`
- **Real-Time Updates**: Configurable crawling intervals
- **Weighted Ranking**: Customizable algorithm to prioritize news sources

### 🔔 Notification System
- **Multiple Channels**: Telegram, Email, Feishu, DingTalk, WeCom, ntfy
- **Smart Batching**: Automatic message batching for large updates
- **Time Windows**: Configure quiet hours to avoid notifications during off-hours
- **Push Modes**:
  - **Daily**: Daily summary of all matching news
  - **Current**: Latest trending topics from current rankings
  - **Incremental**: Only notify when new matching topics appear

### 🤖 MCP Server (AI Integration)
- **13 Powerful Tools** for news query, analytics, and search
- **FastMCP 2.0**: Modern MCP protocol implementation
- **Stdio & HTTP Transports**: Flexible deployment options
- **AI-Ready**: Designed for integration with Claude, ChatGPT, and other AI assistants

#### MCP Tools Categories:
1. **Data Query**: Latest news, historical news, trending topics
2. **Analytics**: Trend analysis, sentiment analysis, platform comparisons
3. **Search**: Keyword search, fuzzy search, entity recognition
4. **System**: Configuration management, status monitoring, manual triggers

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ruslanmv/SignalForge.git
cd SignalForge
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
pip install -e .
```

3. **Configure your keywords**

Edit `config/frequency_words.txt` and add keywords you want to monitor (one per line):
```
AI
Machine Learning
Tesla
SpaceX
Climate Change
```

4. **Configure notifications** (optional)

Edit `config/config.yaml` and add your webhook URLs:
```yaml
notification:
  webhooks:
    telegram_bot_token: "your-bot-token"
    telegram_chat_id: "your-chat-id"
    email_from: "your-email@example.com"
    email_to: "recipient@example.com"
```

⚠️ **Security Warning**: Never commit webhook URLs to public repositories. Use environment variables or GitHub Secrets for sensitive data.

5. **Run the crawler**
```bash
python main.py
```

---

## ⚙️ Configuration

### Main Configuration File: `config/config.yaml`

#### Crawler Settings
```yaml
crawler:
  request_interval: 1000  # Request interval in milliseconds
  enable_crawler: true    # Enable/disable crawling
  use_proxy: false        # Enable proxy if needed
```

#### Report Modes
```yaml
report:
  mode: "daily"  # Options: "daily" | "current" | "incremental"
```

- **daily**: Daily summary of all matching news
- **current**: Current top trending topics
- **incremental**: Only new matches (reduces notification spam)

#### Notification Settings
```yaml
notification:
  enable_notification: true
  push_window:
    enabled: false     # Enable time-based push control
    time_range:
      start: "09:00"   # Start time (24h format)
      end: "18:00"     # End time
    once_per_day: true # Only one notification per day in window
```

---

## 🤖 MCP Server

SignalForge includes a powerful MCP server for AI-assisted news analysis.

### Start MCP Server

**Stdio mode** (for local AI assistants):
```bash
signalforge --transport stdio
```

**HTTP mode** (for production):
```bash
signalforge --transport http --host 0.0.0.0 --port 3333
```

### Available MCP Tools

| Category | Tool | Description |
|----------|------|-------------|
| **Data Query** | `get_latest_news` | Get most recent news batch |
| | `get_news_by_date` | Query news by date |
| | `get_trending_topics` | Get trending keyword statistics |
| **Analytics** | `analyze_topic_trend` | Analyze topic trends over time |
| | `analyze_data_insights` | Platform comparisons and insights |
| | `analyze_sentiment` | Sentiment analysis of news |
| | `find_similar_news` | Find related/similar news items |
| | `generate_summary_report` | Generate daily/weekly reports |
| **Search** | `search_news` | Unified search (keyword/fuzzy/entity) |
| | `search_related_news_history` | Historical related news |
| **System** | `get_current_config` | View system configuration |
| | `get_system_status` | Check system status |
| | `trigger_crawl` | Manually trigger news crawl |

### MCP Client Configuration

For Claude Desktop, add to your config:
```json
{
  "mcpServers": {
    "signalforge": {
      "command": "signalforge",
      "args": ["--transport", "stdio"],
      "env": {
        "SIGNALFORGE_ENV": "production"
      }
    }
  }
}
```

---

## 🐳 Docker Deployment

### Using Docker Compose

1. **Navigate to docker directory**
```bash
cd docker
```

2. **Start the service**
```bash
docker-compose up -d
```

The crawler will run automatically on an hourly schedule using supercronic.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SIGNALFORGE_ENV` | Environment (dev/staging/production) | `production` |
| `SIGNALFORGE_LOG_LEVEL` | Logging level | `INFO` |

---

## 📬 Notification Channels

SignalForge supports multiple notification channels:

### Telegram
```yaml
webhooks:
  telegram_bot_token: "your-bot-token"
  telegram_chat_id: "your-chat-id"
```

### Email
```yaml
webhooks:
  email_from: "sender@example.com"
  email_password: "app-password"
  email_to: "recipient@example.com"
  email_smtp_server: ""  # Auto-detect if empty
  email_smtp_port: ""    # Auto-detect if empty
```

### Feishu / DingTalk / WeCom
```yaml
webhooks:
  feishu_url: "https://open.feishu.cn/open-apis/bot/v2/hook/..."
  dingtalk_url: "https://oapi.dingtalk.com/robot/send?access_token=..."
  wework_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
```

### ntfy
```yaml
webhooks:
  ntfy_server_url: "https://ntfy.sh"  # Or your self-hosted server
  ntfy_topic: "your-topic"
  ntfy_token: ""  # Optional for private topics
```

---

## 📊 Data Storage

All crawled news is stored in the `output/` directory:
```
output/
  ├── 2025-11-24/
  │   └── txt/
  │       ├── 00-30.txt
  │       ├── 01-30.txt
  │       └── ...
  └── 2025-11-25/
      └── txt/
          └── ...
```

Each file contains news from all configured platforms at that timestamp.

---

## 🔧 Advanced Configuration

### Platform Weighting

Adjust the importance of different ranking factors:
```yaml
weight:
  rank_weight: 0.6       # Position in platform rankings
  frequency_weight: 0.3  # Appearance frequency
  hotness_weight: 0.1    # Platform-specific hotness score
```

### Supported Platforms

Current platforms (configurable in `config/config.yaml`):
- Toutiao (Jinri Toutiao)
- Baidu Hot Search
- Weibo
- Zhihu
- Douyin
- Bilibili
- And more...

---

## 📝 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests.

---

## ⚠️ Disclaimer

This tool is for personal news monitoring purposes only. Please respect the terms of service of all news platforms. The developers are not responsible for any misuse of this software.

---

## 📧 Support

For issues and questions, please use the GitHub issue tracker.

---

<div align="center">

**SignalForge** - Forging clear signals from noisy data

Built with ❤️ for the information age

</div>
