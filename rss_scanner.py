#!/usr/bin/env python3
"""
YouTube RSS Feed Scanner - CLI Tool
Generate RSS feeds from YouTube channel, video, or playlist URLs.
Uses Invidious instances for feed generation since YouTube's native feeds are broken.
"""

import argparse
import re
import sys
import urllib.request
import urllib.parse
import json


# Invidious instances to try (open-source YouTube frontends with RSS support)
INVIDIOUS_API_ENDPOINTS = [
    "https://pipedapi.kavin.rocks",
    "https://api.piped.yt",
    "https://api.piped.privacydev.net",
]

# Fallback RSS template (YouTube's native feeds are mostly broken but included as reference)
YOUTUBE_RSS_TEMPLATE = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def get_channel_videos(channel_id: str) -> list[dict]:
    """Fetch recent videos from channel by scraping."""
    try:
        # Get channel home page to find uploads playlist ID
        channel_url = f"https://www.youtube.com/channel/{channel_id}"
        html = fetch_url(channel_url)
        
        # Find uploads playlist ID
        uploads_match = re.search(r'"browseId":"([^"]+)","browseEndpoint":\{" browsePath":"[^"]*\/video', html)
        
        videos = []
        seen_ids = set()
        
        # Extract from videos page
        videos_url = f"https://www.youtube.com/channel/{channel_id}/videos"
        videos_html = fetch_url(videos_url)
        
        vid_pattern = re.compile(r'"videoId":"([a-zA-Z0-9_-]{11})"')
        for vid_match in vid_pattern.finditer(videos_html):
            vid = vid_match.group(1)
            if vid not in seen_ids:
                seen_ids.add(vid)
                videos.append({'videoId': vid, 'title': f'Video {vid}', 'published': ''})
                if len(videos) >= 10:
                    break
        
        return videos
    except Exception:
        return []


def generate_atom_feed(channel_id: str, channel_name: str, videos: list[dict]) -> str:
    """Generate Atom RSS feed from videos."""
    if not videos:
        return ""
    
    feed = f'''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{channel_name or channel_id} - YouTube Videos</title>
  <link rel="alternate" type="text/html" href="https://www.youtube.com/channel/{channel_id}"/>
  <link rel="self" href="https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"/>
  <id>yt:channel:{channel_id}</id>
'''
    for video in videos:
        video_id = video.get('videoId', video.get('url', '').split('=')[-1] if video.get('url') else '')
        title = video.get('title', 'Untitled')
        published = video.get('published', video.get('uploaded', ''))
        thumbnail = video.get('thumbnail', '')
        
        feed += f'''  <entry>
    <title>{title}</title>
    <link rel="alternate" type="text/html" href="https://www.youtube.com/watch?v={video_id}"/>
    <id>yt:video:{video_id}</id>
    <updated>{published}</updated>
    <author>
      <name>{channel_name or channel_id}</name>
    </author>
  </entry>
'''
    
    feed += '</feed>'
    return feed

PATTERNS = [
    (r"/channel/([a-zA-Z0-9_-]{22})", "channel"),
    (r"/c/([a-zA-Z0-9_-]+)", "custom"),
    (r"/user/([a-zA-Z0-9_-]+)", "user"),
    (r"/@([a-zA-Z0-9_-]+)", "handle"),
    (r"/watch\?v=([a-zA-Z0-9_-]{11})", "video"),
    (r"youtu\.be/([a-zA-Z0-9_-]{11})", "short"),
    (r"/live/([a-zA-Z0-9_-]+)", "live"),
    (r"/playlist\?list=([a-zA-Z0-9_-]+)", "playlist"),
]


def fetch_url(url: str) -> str:
    """Fetch URL content using direct request."""
    req = urllib.request.Request(
        url, 
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode('utf-8')


def fetch_oembed(url: str) -> dict:
    """Fetch video info using oEmbed API."""
    oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
    req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode('utf-8'))


def fetch_noembed(url: str) -> dict:
    """Fetch channel info using Noembed API."""
    noembed_url = f"https://noembed.com/embed?url={url}"
    req = urllib.request.Request(noembed_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode('utf-8'))


def extract_channel_id(url: str) -> tuple[str | None, str | None]:
    """Extract channel ID from YouTube URL."""
    url = url.strip()
    if not url.startswith('http'):
        url = 'https://' + url
    
    if 'youtube.com' not in url and 'youtu.be' not in url:
        raise ValueError("Invalid YouTube URL")
    
    # Match URL pattern
    matched_id = None
    url_type = None
    
    for pattern, ptype in PATTERNS:
        match = re.search(pattern, url)
        if match:
            matched_id = match.group(1)
            url_type = ptype
            break
    
    if not matched_id:
        raise ValueError("Could not parse YouTube URL")
    
    # Direct channel ID
    if url_type == "channel":
        return matched_id, None
    
    # Handle types that need fetching
    # For video URLs, try noembed which provides channel URL
    if url_type in ("video", "short"):
        try:
            video_url = f"https://www.youtube.com/watch?v={matched_id}"
            noembed = fetch_noembed(video_url)
            author_url = noembed.get('author_url', '')
            if author_url:
                # author_url gives us the channel handle URL
                # Try to fetch that to get channel ID
                try:
                    html = fetch_url(author_url)
                    # Try externalId first
                    channel_match = re.search(r'"externalId":"([^"]+)"', html)
                    if channel_match:
                        return channel_match.group(1), noembed.get('title', '')
                    # Fall back to channelId
                    channel_match = re.search(r'"channelId":"([a-zA-Z0-9_-]{22})"', html)
                    if channel_match:
                        return channel_match.group(1), noembed.get('title', '')
                except:
                    pass
        except Exception as e:
            print(f"noembed error: {e}", file=sys.stderr)
    
    # Try noembed for @username URLs (alternative when direct fetch has issues)
    if url_type == "handle":
        # Try noembed first
        try:
            noembed = fetch_noembed(url)
            author_url = noembed.get('author_url', '')
            if author_url:
                html = fetch_url(author_url)
                channel_match = re.search(r'"externalId":"([^"]+)"', html)
                if channel_match:
                    return channel_match.group(1), noembed.get('title', '')
        except Exception as e:
            print(f"noembed error: {e}", file=sys.stderr)
        
        # Fallback: direct HTML fetch 
        try:
            html = fetch_url(url)
            channel_match = re.search(r'"externalId":"([^"]+)"', html)
            if channel_match:
                return channel_match.group(1), None
            channel_match = re.search(r'"channelId":"([a-zA-Z0-9_-]{22})"', html)
            if channel_match:
                return channel_match.group(1), None
        except Exception as e:
            print(f"direct fetch error: {e}", file=sys.stderr)
    
    # Try direct fetch - works from server-side Python
    fetch_urls = []
    
    if url_type in ("custom", "user", "handle"):
        fetch_urls.append(url)
    elif url_type in ("video", "short"):
        video_id = matched_id
        fetch_urls.append(f"https://www.youtube.com/watch?v={video_id}")
    elif url_type == "live":
        fetch_urls.append(f"https://www.youtube.com/live/{matched_id}")
    elif url_type == "playlist":
        fetch_urls.append(f"https://www.youtube.com/playlist?list={matched_id}")
    
    # Try fetching to get channel ID
    for fetch_url_str in fetch_urls:
        try:
            html = fetch_url(fetch_url_str)
            
            # Try externalId first (more reliable)
            channel_match = re.search(r'"externalId":"([^"]+)"', html)
            if channel_match:
                return channel_match.group(1), None
            
            # Look for channelId in JSON
            channel_match = re.search(r'"channelId":"([a-zA-Z0-9_-]{22})"', html)
            if channel_match:
                channel_id = channel_match.group(1)
                name_match = re.search(r'"channelName":"([^"]+)"', html)
                channel_name = name_match.group(1) if name_match else None
                return channel_id, channel_name
        except Exception as e:
            print(f"Warning: Failed to fetch {fetch_url_str}: {e}", file=sys.stderr)
            continue
    
    raise ValueError("Could not find channel ID from URL")


def get_rss_feed(url: str, include_api_endpoints: bool = False, base_url: str = "http://localhost:8080") -> tuple:
    """Get RSS feed data for a YouTube channel.
    
    Returns: (youtube_rss, channel_id, channel_name, atom_feed, video_count, invidious_rss, api_endpoints)
    """
    channel_id, channel_name = extract_channel_id(url)
    
    # YouTube's native RSS URL (mostly broken but included for reference)
    youtube_rss = YOUTUBE_RSS_TEMPLATE.format(channel_id=channel_id)
    
    # Try to get videos from YouTube channel page
    videos = get_channel_videos(channel_id)
    video_count = len(videos)
    
    # Generate Atom feed if we got videos
    atom_feed = generate_atom_feed(channel_id, channel_name, videos) if videos else ""
    
    # Check for working Invidious RSS feed
    invidious_rss = None
    for instance in INVIDIOUS_API_ENDPOINTS:
        try:
            test_url = f"{instance}/channel/{channel_id}"
            req = urllib.request.Request(test_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    invidious_rss = f"{instance}/feed/channel/{channel_id}"
                    break
        except Exception:
            continue
    
    api_endpoints = {}
    if include_api_endpoints:
        encoded_url = urllib.parse.quote(url, safe="")
        api_endpoints = {
            "json_api": f"{base_url.rstrip('/')}/api/feed",
            "atom_feed_path": f"{base_url.rstrip('/')}/feed/{encoded_url}",
            "atom_feed_query": f"{base_url.rstrip('/')}/feed?channel_url={encoded_url}",
        }

    return youtube_rss, channel_id, channel_name, atom_feed, video_count, invidious_rss, api_endpoints


def main():
    parser = argparse.ArgumentParser(
        description="YouTube RSS Feed Scanner - Generate RSS feeds from YouTube URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rss_scanner.py https://www.youtube.com/@GoogleDevelopers
  python rss_scanner.py https://www.youtube.com/watch?v=dQw4w9WgXcQ
  python rss_scanner.py https://www.youtube.com/c/MarquesBrownlee
  python rss_scanner.py https://youtu.be/dQw4w9WgXcQ
  python rss_scanner.py "https://www.youtube.com/playlist?list=PL590L1qF-2kDbVW3VbDyDdUP8T5RI-3a3"

Supported URL types:
  - Channel: @username, /c/name, /user/name, /channel/UC...
  - Video:   watch?v=ID, youtu.be/ID
  - Live:    /live/username
  - Playlist: ?list=PLAYLIST_ID
        """
    )
    parser.add_argument("url", nargs="?", help="YouTube channel, video, or playlist URL")
    parser.add_argument("-q", "--quiet", action="store_true", help="Only output the RSS URL")
    parser.add_argument("-c", "--copy", action="store_true", help="Copy RSS URL to clipboard")
    parser.add_argument("-a", "--atom", action="store_true", help="Output generated Atom RSS feed")
    parser.add_argument("--include-api-endpoints", action="store_true", help="Include API endpoint URLs in output")
    parser.add_argument("--base-url", default="http://localhost:8080", help="Base URL used for API endpoint output")
    
    args = parser.parse_args()
    
    # Prompt for URL if not provided
    url = args.url
    if not url:
        url = input("Enter YouTube channel URL: ").strip()
        if not url:
            print("Error: No URL provided", file=sys.stderr)
            sys.exit(1)
    
    # Add https:// if missing
    if not url.startswith("http"):
        url = "https://" + url
    
    try:
        youtube_rss, channel_id, channel_name, atom_feed, video_count, invidious_rss, api_endpoints = get_rss_feed(
            url,
            include_api_endpoints=args.include_api_endpoints,
            base_url=args.base_url
        )
        
        if args.atom:
            # Output generated Atom feed directly
            if atom_feed:
                print(atom_feed)
            else:
                print(f"Error: Could not fetch videos from channel", file=sys.stderr)
                sys.exit(1)
        elif args.quiet:
            # In quiet mode, output working feed URL
            if atom_feed:
                print(f"Generated Atom feed ({video_count} videos)")
            else:
                print(youtube_rss)
        else:
            if channel_name:
                print(f"Channel: {channel_name}")
            print(f"Channel ID: {channel_id}")
            print(f"\nYouTube RSS: {youtube_rss}")
            if invidious_rss:
                print(f"Invidious RSS: {invidious_rss}")
            if atom_feed:
                print(f"Generated Feed: {video_count} videos available")
                print("Use -a flag to output Atom XML feed")
            else:
                print("\nNote: YouTube's native feeds are broken.")
            if api_endpoints:
                print("\nAPI Endpoints:")
                print(f"JSON API (POST): {api_endpoints['json_api']}")
                print(f"Atom Feed (path): {api_endpoints['atom_feed_path']}")
                print(f"Atom Feed (query): {api_endpoints['atom_feed_query']}")
        
        if args.copy:
            # Copy YouTube RSS URL (even if potentially broken)
            try:
                import subprocess
                if sys.platform == "darwin":
                    subprocess.run(["pbcopy"], input=youtube_rss, check=True)
                elif sys.platform == "linux":
                    subprocess.run(["xclip", "-selection", "clipboard"], input=youtube_rss, check=True)
                elif sys.platform == "win32":
                    subprocess.run(["cmd", "/c", "echo", youtube_rss, "|", "clip"], check=True)
                if not args.quiet:
                    print("\nCopied to clipboard!")
            except Exception:
                pass  # Clipboard not available
                
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
