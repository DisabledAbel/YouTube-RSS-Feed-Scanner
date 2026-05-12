# YouTube RSS Feed Scanner

A Python CLI tool that generates RSS feeds from YouTube channel URLs. Can be deployed to Vercel for web access.

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

Add the following environment variable in Vercel dashboard:
- `PYTHONUNBUFFERED`: `1`

### Local Development

```bash
pip install flask flask-caching
python -m api.app
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Web UI |
| `/feed/<channel_url>` | GET | RSS feed (cached 5 min) |
| `/feed/<channel_url>` | GET | RSS feed XML (cached) |
| `/api/feed` | POST | JSON API |

## Usage

### Web UI
Open the deployed URL and enter a YouTube channel URL.

### API

```bash
# Get feed via API
curl -X POST https://your-app.vercel.app/api/feed \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/@ChannelName"}'
```

### RSS Reader
Subscribe to:
```
https://your-app.vercel.app/feed/https://www.youtube.com/@ChannelName
```

The feed updates every 5 minutes.

## CLI Usage

Run without arguments for interactive prompt:

```bash
python rss_scanner.py
Enter YouTube channel URL: https://www.youtube.com/@ChannelName
```

Or pass URL directly:

```bash
python rss_scanner.py "https://www.youtube.com/@ChannelName"
```

## Supported URL Types

- **Handle**: `https://www.youtube.com/@username`
- **Custom**: `https://www.youtube.com/c/ChannelName`
- **User**: `https://www.youtube.com/user/username`
- **Channel**: `https://www.youtube.com/channel/UC...`
- **Video**: `https://www.youtube.com/watch?v=...` or `https://youtu.be/...`
- **Playlist**: `https://www.youtube.com/playlist?list=...`

## Options

| Flag | Description |
|------|-------------|
| `-q`, `--quiet` | Only output the RSS URL |
| `-c`, `--copy` | Copy RSS URL to clipboard |
| `-a`, `--atom` | Output generated Atom RSS feed |

## Examples

```bash
# Interactive mode (prompts for URL)
python rss_scanner.py

# Basic usage
python rss_scanner.py "https://www.youtube.com/@GoogleDevelopers"

# Get Atom feed for RSS readers
python rss_scanner.py "https://www.youtube.com/@t3dotgg" -a

# Quiet mode (for scripts)
python rss_scanner.py "https://www.youtube.com/c/MarquesBrownlee" -q
```

## Output

```
Channel ID: UC_x5XG1OV2P6uZZ5FSM9Ttw

YouTube RSS (often broken): https://www.youtube.com/feeds/videos.xml?channel_id=UC_x5XG1OV2P6uZZ5FSM9Ttw
Generated Feed: 10 videos available
Use -a flag to output Atom XML feed
```

## Notes

- YouTube's native RSS feeds (`youtube.com/feeds/...`) often return 401/404 errors
- This tool generates working Atom RSS feeds by extracting video data from channel pages
- Run with `-a` to get a usable feed for any RSS reader
