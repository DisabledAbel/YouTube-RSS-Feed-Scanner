# YouTube RSS Feed Scanner

## Features

- Scan YouTube RSS feeds without the YouTube API
- Detect newly uploaded videos
- Parse channel and playlist feeds
- Lightweight and fast
- Works with:
  - Channel URLs
  - `@handles`
  - Channel IDs
  - Playlist URLs
- JSON output support
- Optional Discord webhook notifications
- Easy to self-host
- Perfect for:
  - RSS readers
  - Automation tools
  - Archiving workflows

---

## Why?

YouTube still provides RSS feeds for channels and playlists, making it possible to track uploads without using the official API.

This project makes it easy to:

- Convert YouTube URLs into RSS feeds
- Monitor channels for new uploads
- Build automation around YouTube content
- Avoid API quotas and API keys
- Integrate YouTube feeds into custom workflows

---

# Run Locally

Get the project running in just a few minutes.

---

## 1. Clone the repository

```bash
git clone https://github.com/DisabledAbel/YouTube-RSS-Feed-Scanner.git
```

---

## 2. Enter the project folder

```bash
cd YouTube-RSS-Feed-Scanner
```

---

## 3. Install dependencies

### Option A: Using Python (Recommended)
```bash
pip install -r requirements.txt
```

### Option B: Using npm
```bash
npm install
```

---

## 4. Start the project

### Option A: Using Python
Start local web server:
```bash
python api/app.py
```

### Option B: Using npm
Start local web server:
```bash
npm start
```
---

### `/api/monitor` (GET or POST)

Advanced feed monitoring with health checks and scoring.

**Parameters:**
- `url`: The RSS feed URL to monitor.

**Example Request:**
```bash
curl "https://your-domain.com/api/monitor?url=https://www.youtube.com/feeds/videos.xml?channel_id=UC123"
```

**Example Response:**
```json
{
  "feedUrl": "https://www.youtube.com/feeds/videos.xml?channel_id=UC123",
  "responseTimeMs": 421,
  "score": 92,
  "health": {
    "status": "healthy",
    "reason": null
  },
  "lastUpdated": {
    "iso": "2026-06-08T10:30:00+00:00",
    "relative": "3 hours ago"
  }
}
```

---

### `/api/feed` (GET or POST)

### Scan a YouTube channel

```bash
npm start "https://www.youtube.com/@LinusTechTips"
```

### GET endpoint (works directly in browser)

```text
/api/feed?url=https://www.youtube.com/@LinusTechTips
```

---

### `/feed/<type>/<channel_url>` (GET)

### Get RSS feed via URL path

Access a YouTube channel's RSS feed by passing the channel URL in the path.

Supported feed types:

- `all` (existing combined behavior)
- `videos` (regular videos tab)
- `shorts` (shorts tab)
- `live` (live/streams tab)

Endpoint examples:

```text
/feed/all/:channel
/feed/videos/:channel
/feed/shorts/:channel
/feed/live/:channel
```

**Important:** The `channel_url` parameter must be URL-encoded (percent-encoded) to avoid 404 errors.

**Example with encoding:**

```javascript
// URL-encode the full YouTube URL
const channelUrl = 'https://www.youtube.com/channel/UCXuqSBlHAE6Xw-yeJA0Tunw';
const encodedUrl = encodeURIComponent(channelUrl);
// Result: https%3A%2F%2Fwww.youtube.com%2Fchannel%2FUCXuqSBlHAE6Xw-yeJA0Tunw

// Use in request
fetch(`/feed/videos/${encodedUrl}`)
```

**Alternative (recommended):** Use URL-encoded paths to avoid encoding issues:

```bash
/feed/all/https%3A%2F%2Fwww.youtube.com%2Fchannel%2FUCXuqSBlHAE6Xw-yeJA0Tunw
```

---

### Scan a playlist

```bash
npm start "https://www.youtube.com/playlist?list=PLxxxxxxxx"
```

---

### Output JSON

```bash
npm start --json
```

### Include API endpoints in terminal output

```bash
python rss_scanner.py "https://www.youtube.com/@LinusTechTips" --include-api-endpoints --base-url "https://your-domain.com"
```

### Send feed info to Discord webhook (web UI / API)

Pass `discord_webhook_url` to `/api/feed` and the app will send a message to Discord with channel info and the generated RSS URL.

```json
{
  "url": "https://www.youtube.com/@LinusTechTips",
  "discord_webhook_url": "https://discord.com/api/webhooks/..."
}
```

---


## CLI RSS Reader (Python)

If you are running locally and want to read recent items directly in the terminal:

1. **Use Python 3.10+** (type hints in this project require modern Python).
2. **Run the scanner with a YouTube URL plus `--read`.**
3. **Optionally set `--limit`** to control how many entries are printed.

### Basic reader command

```bash
python rss_scanner.py "https://www.youtube.com/@LinusTechTips" --read
```

### Show only the latest 5 entries

```bash
python rss_scanner.py "https://www.youtube.com/@LinusTechTips" --read --limit 5
```

### Reader with API endpoint output

```bash
python rss_scanner.py "https://www.youtube.com/@LinusTechTips" --read --include-api-endpoints --base-url "http://localhost:8080"
```

### Troubleshooting

- If YouTube lookups fail, verify outbound internet access from your machine/container.
- The reader prefers a discovered Invidious feed and falls back to YouTube RSS when needed.
- If you get no entries, try a different channel URL and increase `--limit`.

---

## Example RSS Feed

```text
https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxxxxxx
```

---

## Example Output

```json
{
  "title": "New Video Title",
  "videoId": "abc123",
  "published": "2026-05-11T12:00:00Z",
  "channel": "Example Channel"
}
```

---

## Use Cases

### RSS Readers

Track uploads in:

- Feedly
- FreshRSS
- Miniflux
- NewsBlur

---

### Archiving

Monitor and archive newly uploaded videos automatically.

---

# Cloud Deployment 

## Vercel

Deploy instantly with Vercel.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/import?buildCommand=uv+pip+install+--system+-r+requirements.txt&framework=flask&hasTrialAvailable=1&id=1236109409&installCommand=uv+pip+install+--system+-r+requirements.txt&name=YouTube-RSS-Feed-Scanner&outputDirectory=api&owner=DisabledAbel&project-name=you-tube-rss-feed-scanner&provider=github&remainingProjects=1&s=https%3A%2F%2Fgithub.com%2FDisabledAbel%2FYouTube-RSS-Feed-Scanner)

---

# Contributing

Pull requests are welcome.

If you find a bug or want a feature added, open an issue.

---

# Disclaimer

This project is not affiliated with or endorsed by YouTube or Google.

Users are responsible for complying with YouTube’s Terms of Service.
