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

```bash
npm install
```

---

## 4. Start the project

```bash
npm start
```
---

### `/api/feed` (POST)

### Scan a YouTube channel

```bash
npm start "https://www.youtube.com/@LinusTechTips"
```

---

### `/feed/<channel_url>` (GET)

### Get RSS feed via URL path

Access a YouTube channel's RSS feed by passing the channel URL in the path.

**Important:** The `channel_url` parameter must be URL-encoded (percent-encoded) to avoid 404 errors.

**Example with encoding:**

```javascript
// URL-encode the full YouTube URL
const channelUrl = 'https://www.youtube.com/channel/UCXuqSBlHAE6Xw-yeJA0Tunw';
const encodedUrl = encodeURIComponent(channelUrl);
// Result: https%3A%2F%2Fwww.youtube.com%2Fchannel%2FUCXuqSBlHAE6Xw-yeJA0Tunw

// Use in request
fetch(`/feed/${encodedUrl}`)
```

**Alternative (recommended):** Use query parameters to avoid encoding issues:

```bash
/feed?channel_url=https://www.youtube.com/channel/UCXuqSBlHAE6Xw-yeJA0Tunw
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

# Deployment

## Vercel

Deploy instantly with Vercel.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/import)

---

# Contributing

Pull requests are welcome.

If you find a bug or want a feature added, open an issue.

---

# Disclaimer

This project is not affiliated with or endorsed by YouTube or Google.

Users are responsible for complying with YouTube’s Terms of Service.
