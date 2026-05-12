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
- GitHub Actions compatible
- Perfect for:
  - RSS readers
  - IPTV systems
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

## Requirements

Before starting, make sure you have:

- Node.js 18+
- npm
- Git

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

If the project supports development mode:

```bash
npm run dev
```

---

## Usage

### Scan a YouTube channel

```bash
npm start "https://www.youtube.com/@LinusTechTips"
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
