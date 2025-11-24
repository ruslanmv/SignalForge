Here is the English-only version of the Usage Q\&A guide.

# SignalForge MCP Tool Usage Q\&A

> AI Prompting Guide - How to Use the News Trend Analysis Tool via Conversation

## ⚙️ Default Settings (Important\!)

The following optimization strategies are adopted by default, primarily to save AI token consumption:

| Default Setting | Description | How to Adjust |
| :--- | :--- | :--- |
| **Limit Count** | Returns 50 news items by default. | Say "return the top 10" or "give me 100 items" in the chat. |
| **Time Range** | Queries today's data by default. | Say "query yesterday," "last week," or "Jan 1st to 7th." |
| **URL Links** | Links are **not** returned by default (saves \~160 tokens/item). | Say "need links" or "include URLs." |
| **Keyword List** | Does not use `frequency_words.txt` to filter news by default. | Only used when calling the "Trending Topics" tool. |

**⚠️ Important:** The choice of AI model directly affects the tool's performance. The smarter the AI, the more accurate the calls. When you lift the restrictions above (e.g., expanding from a daily query to a weekly query), first ensure you have a week's worth of data locally. Secondly, token consumption may multiply (though not necessarily; if you analyze the trend of 'Apple' over a week and there isn't much news, consumption might remain low).

**💡 Tip:** When you say "last 7 days," the AI automatically calculates the corresponding date range (e.g., 2025-10-18 to 2025-10-25) and passes it to the tool.

-----

## 💰 AI Models

Below, I will use the **[SiliconFlow](https://cloud.siliconflow.cn)** platform as an example, which offers many large models. During the development and testing of this project, I conducted extensive functional testing and verification using this platform.

### 📊 Registration Method Comparison

| Registration Method | Direct Registration (No Invite) | Registration via Invite Link |
| :---: | :---: | :---: |
| Link | [siliconflow.cn](https://cloud.siliconflow.cn) | [Invite Link](https://cloud.siliconflow.cn/i/fqnyVaIU) |
| Free Quota | 0 tokens | **20 Million tokens** (≈14 CNY) |
| Extra Benefit | ❌ | ✅ The inviter also gets 20M tokens |

> 💡 **Tip**: The free quota mentioned above should be enough for **over 200 queries**.

### 🚀 Quick Start

#### 1️⃣ Register and Get API Key

1.  Complete registration using the link above.
2.  Visit the [API Key Management Page](https://cloud.siliconflow.cn/me/account/ak).
3.  Click "New API Key".
4.  Copy the generated key (keep it safe).

#### 2️⃣ Configure in Cherry Studio

1.  Open **Cherry Studio**.
2.  Go to "Model Service" settings.
3.  Find "SiliconFlow" (硅基流动).
4.  Paste the copied key into the **[API Key]** input box.
5.  Ensure the checkbox in the top right corner is checked and shows as **Green** ✅.

-----

### ✨ Configuration Complete\!

You can now start using this project and enjoy stable, fast AI services\!

After testing your first query, please immediately check your [SiliconFlow Billing](https://cloud.siliconflow.cn/me/bills) to see the consumption for that query so you have an estimate in mind.

-----

## Basic Queries

### Q1: How do I view the latest news?

**You can ask:**

  * "Show me the latest news."
  * "Query today's hot news."
  * "Get the latest 10 news items from Zhihu and Weibo."
  * "View latest news, include links."

**Tool Called:** `get_latest_news`

**Tool Return Behavior:**

  * The MCP tool returns the latest 50 news items from all platforms to the AI.
  * Does not include URL links (to save tokens).

**AI Display Behavior (Important):**

  * ⚠️ **The AI usually summarizes automatically**, showing only part of the news (e.g., TOP 10-20 items).
  * ✅ If you want to see all 50 items, you need to explicitly ask: "Show all news" or "List all 50 items completely."
  * 💡 This is natural AI behavior, not a tool limitation.

**Adjustments:**

  * Specify platform: e.g., "Only look at Zhihu."
  * Adjust quantity: e.g., "Return top 20."
  * Include links: e.g., "Need links."
  * **Request full display**: e.g., "Show all, do not summarize."

-----

### Q2: How do I query news for a specific date?

**You can ask:**

  * "Query yesterday's news."
  * "Check Zhihu news from 3 days ago."
  * "What news is there for 2025-10-10?"
  * "News from last Monday."
  * "Show me the latest news" (automatically queries today).

**Tool Called:** `get_news_by_date`

**Supported Date Formats:**

  * Relative: Today, yesterday, day before yesterday, 3 days ago.
  * Weekdays: Last Monday, this Wednesday.
  * Absolute: 2025-10-10, Oct 10th.

**Tool Return Behavior:**

  * Automatically queries today if no date is specified (saves tokens).
  * The MCP tool returns 50 news items from all platforms to the AI.
  * Does not include URL links.

**AI Display Behavior (Important):**

  * ⚠️ **The AI usually summarizes automatically**, showing only part of the news.
  * ✅ If you want to see everything, explicitly ask: "Show all news, do not summarize."

-----

### Q3: How do I view frequency statistics for topics I follow?

**You can ask:**

  * "How many times did the words I follow appear today?"
  * "See which words in my watchlist are most popular."
  * "Calculate the frequency of keywords in `frequency_words.txt`."

**Tool Called:** `get_trending_topics`

**Important Note:**

  * This tool does **NOT** automatically extract general news trends.
  * Instead, it counts the **personal keywords** you set in `config/frequency_words.txt`.
  * This is a **customizable** list; you can add keywords based on your interests.

-----

## Search & Retrieval

### Q4: How do I search for news containing specific keywords?

**You can ask:**

  * "Search for news containing 'Artificial Intelligence'."
  * "Find reports about 'Tesla price cut'."
  * "Search for Musk-related news, return top 20."
  * "Find news about 'iPhone 16' from the last 7 days."
  * "Find news related to 'Tesla' from Jan 1st to Jan 7th, 2025."
  * "Find the link for the 'iPhone 16 release' news."

**Tool Called:** `search_news`

**Tool Return Behavior:**

  * Uses keyword mode search.
  * Defaults to searching today's data.
  * AI automatically converts relative time like "last 7 days" or "last week" into specific date ranges.
  * The MCP tool returns a maximum of 50 results to the AI.
  * Does not include URL links.

**AI Display Behavior (Important):**

  * ⚠️ **The AI usually summarizes automatically**, showing only part of the search results.
  * ✅ If you want to see everything, explicitly ask: "Show all search results."

**Adjustments:**

  * Specify time range:
      * Relative: "Search last week's" (AI calculates dates).
      * Absolute: "Search from Jan 1, 2025 to Jan 7, 2025."
  * Specify platform: e.g., "Search only Zhihu."
  * Adjust sorting: e.g., "Sort by weight."
  * Include links: e.g., "Need links."

**Example Dialogue:**

```
User: Search for news about "AI Breakthrough" from the last 7 days.
AI: (Calculates automatically: date_range={"start": "2025-10-18", "end": "2025-10-25"})

User: Find reports on "Tesla" in January 2025.
AI: (date_range={"start": "2025-01-01", "end": "2025-01-31"})
```

-----

### Q5: How do I find historical related news?

**You can ask:**

  * "Find news related to 'AI Breakthrough' from yesterday."
  * "Search for historical reports on 'Tesla' from last week."
  * "Find news related to 'ChatGPT' from last month."
  * "Look for historical news related to 'iPhone Event'."

**Tool Called:** `search_related_news_history`

**Tool Return Behavior:**

  * Searches yesterday's data.
  * Similarity threshold: 0.4.
  * The MCP tool returns a maximum of 50 results to the AI.
  * Does not include URL links.

**AI Display Behavior (Important):**

  * ⚠️ **The AI usually summarizes automatically**, showing only part of the related news.
  * ✅ If you want to see everything, explicitly ask: "Show all related news."

-----

## Trend Analysis

### Q6: How do I analyze the popularity trend of a topic?

**You can ask:**

  * "Analyze the popularity trend of 'Artificial Intelligence' over the last week."
  * "See if the 'Tesla' topic is a flash in the pan or a sustained hot topic."
  * "Detect which topics suddenly exploded today."
  * "Predict potential upcoming hot topics."
  * "Analyze the lifecycle of 'Bitcoin' in December 2024."

**Tool Called:** `analyze_topic_trend`

**Tool Return Behavior:**

  * Supports multiple analysis modes: Trend, Lifecycle, Anomaly Detection, Prediction.
  * AI automatically converts relative time like "last week" to specific date ranges.
  * Defaults to analyzing the last 7 days of data.
  * Statistics are granular by day.

**AI Display Behavior:**

  * Usually displays trend analysis results and charts.
  * AI may summarize key findings.

**Example Dialogue:**

```
User: Analyze the lifecycle of 'Artificial Intelligence' over the last week.
AI: (Calculates automatically: date_range={"start": "2025-10-18", "end": "2025-10-25"})

User: See if 'Bitcoin' was a flash in the pan or a sustained trend in December 2024.
AI: (date_range={"start": "2024-12-01", "end": "2024-12-31"})
```

-----

## Data Insights

### Q7: How do I compare topic attention across different platforms?

**You can ask:**

  * "Compare the attention given to the 'AI' topic across platforms."
  * "See which platform updates most frequently."
  * "Analyze which keywords often appear together."

**Tool Called:** `analyze_data_insights`

**Three Insight Modes:**

| Mode | Function | Example Question |
| :--- | :--- | :--- |
| **Platform Comparison** | Compares attention across platforms. | "Compare attention on 'AI' across platforms." |
| **Activity Stats** | Statistics on platform posting frequency. | "See which platform updates most frequently." |
| **Keyword Co-occurrence** | Analyzes keyword associations. | "Which keywords often appear together?" |

**Tool Return Behavior:**

  * Platform comparison mode.
  * Analyzes today's data.
  * Keyword co-occurrence minimum frequency: 3 times.

**AI Display Behavior:**

  * Usually displays analysis results and statistical data.
  * AI may summarize insights found.

-----

## Sentiment Analysis

### Q8: How do I analyze the sentiment of news?

**You can ask:**

  * "Analyze the sentiment of today's news."
  * "See if 'Tesla' related news is positive or negative."
  * "Analyze the emotional attitude of each platform towards 'Artificial Intelligence'."
  * "Check the sentiment of 'Bitcoin' over the week, select the top 20 most important items."

**Tool Called:** `analyze_sentiment`

**Tool Return Behavior:**

  * Analyzes today's data.
  * The MCP tool returns a maximum of 50 news items to the AI.
  * Sorted by weight (prioritizes important news).
  * Does not include URL links.

**AI Display Behavior (Important):**

  * ⚠️ This tool returns **AI Prompts**, not the direct sentiment analysis result.
  * The AI generates a sentiment analysis report based on these prompts.
  * Usually displays sentiment distribution, key findings, and representative news.

**Adjustments:**

  * Specify topic: e.g., "About 'Tesla'."
  * Specify time: e.g., "Last week."
  * Adjust quantity: e.g., "Return top 20."

-----

### Q9: How do I find similar news reports?

**You can ask:**

  * "Find news similar to 'Tesla price cut'."
  * "Find similar reports about the iPhone launch."
  * "See if there are any reports similar to this news."
  * "Find similar news, need links."

**Tool Called:** `find_similar_news`

**Tool Return Behavior:**

  * Similarity threshold: 0.6.
  * The MCP tool returns a maximum of 50 results to the AI.
  * Does not include URL links.

**AI Display Behavior (Important):**

  * ⚠️ **The AI usually summarizes automatically**, showing only part of the similar news.
  * ✅ If you want to see everything, explicitly ask: "Show all similar news."

-----

### Q10: How do I generate daily or weekly trend summaries?

**You can ask:**

  * "Generate today's news summary report."
  * "Give me a hot topic summary for this week."
  * "Generate a news analysis report for the past 7 days."

**Tool Called:** `generate_summary_report`

**Report Types:**

  * Daily Summary: Summarizes hot news of the day.
  * Weekly Summary: Summarizes trend hotspots of the week.

-----

## System Management

### Q11: How do I view the system configuration?

**You can ask:**

  * "View current system configuration."
  * "Show config file content."
  * "What platforms are available?"
  * "What is the current weight configuration?"

**Tool Called:** `get_current_config`

**Can Query:**

  * Available platform list.
  * Crawler config (request interval, timeout settings).
  * Weight config (ranking weight, frequency weight).
  * Notification config (DingTalk, WeChat).

-----

### Q12: How do I check the system running status?

**You can ask:**

  * "Check system status."
  * "Is the system running normally?"
  * "When was the last crawl?"
  * "How many days of historical data are there?"

**Tool Called:** `get_system_status`

**Returns Information:**

  * System version and status.
  * Last crawl time.
  * Days of historical data.
  * Health check results.

-----

### Q13: How do I manually trigger a crawl task?

**You can ask:**

  * "Please crawl the current news from Toutiao." (Temporary query)
  * "Help me grab the latest news from Zhihu and Weibo and save it." (Persistence)
  * "Trigger a crawl and save the data." (Persistence)
  * "Get real-time data from 36Kr but don't save it." (Temporary query)

**Tool Called:** `trigger_crawl`

**Two Modes:**

| Mode | Purpose | Example |
| :--- | :--- | :--- |
| **Temporary Crawl** | Returns data but does not save. | "Crawl Toutiao news." |
| **Persistent Crawl** | Saves to the `output` folder. | "Grab and save Zhihu news." |

**Tool Return Behavior:**

  * Temporary crawl mode (unsaved).
  * Crawls all platforms.
  * Does not include URL links.

**AI Display Behavior (Important):**

  * ⚠️ **The AI usually summarizes the crawl results**, showing only part of the news.
  * ✅ If you want to see everything, explicitly ask: "Show all crawled news."

**Adjustments:**

  * Specify platform: e.g., "Only crawl Zhihu."
  * Save data: Say "and save" or "save to local."
  * Include links: Say "need links."

-----

## 💡 Usage Tips

### 1\. How do I make the AI show all data instead of automatically summarizing?

**Context**: Sometimes the AI automatically summarizes the data and shows only part of the content, even if the tool returned the full 50 items.

**If the AI still summarizes, you can:**

  * **Method 1 - Explicit Request**: "Please show all news, do not summarize."
  * **Method 2 - Specify Quantity**: "Show all 50 news items."
  * **Method 3 - Question the Behavior**: "Why did you only show 15 items? I want to see them all."
  * **Method 4 - State in Advance**: "Query today's news, display all results completely."

**Note**: The AI may still adjust the display based on context.

### 2\. How do I combine multiple tools?

**Example: Deep analysis of a topic**

1.  Search first: "Search for news related to 'Artificial Intelligence'."
2.  Then analyze trends: "Analyze the popularity trend of 'Artificial Intelligence'."
3.  Finally, sentiment analysis: "Analyze the sentiment of 'Artificial Intelligence' news."

**Example: Tracking an event**

1.  View latest: "Query news about 'iPhone' today."
2.  Find history: "Find historical news related to 'iPhone' from last week."
3.  Find similar reports: "Find news similar to 'iPhone launch event'."

