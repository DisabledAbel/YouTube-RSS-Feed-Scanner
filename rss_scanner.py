#!/usr/bin/env python3
"""
YouTube RSS Feed Scanner - CLI Tool
Generate official RSS feeds from YouTube channel, video, or playlist URLs.
"""

import argparse
import re
import sys
import urllib.request
import urllib.parse
import json


YOUTUBE_RSS_TEMPLATE = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

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
    
    # Try noembed for @username URLs
    if url_type == "handle":
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


def get_rss_feed(url: str) -> str:
    """Get RSS feed URL for a YouTube channel."""
    channel_id, channel_name = extract_channel_id(url)
    
    rss_url = YOUTUBE_RSS_TEMPLATE.format(channel_id=channel_id)
    
    return rss_url, channel_id, channel_name


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
    parser.add_argument("url", help="YouTube channel, video, or playlist URL")
    parser.add_argument("-q", "--quiet", action="store_true", help="Only output the RSS URL")
    parser.add_argument("-c", "--copy", action="store_true", help="Copy RSS URL to clipboard")
    
    args = parser.parse_args()
    
    try:
        rss_url, channel_id, channel_name = get_rss_feed(args.url)
        
        if args.quiet:
            print(rss_url)
        else:
            if channel_name:
                print(f"Channel: {channel_name}")
            print(f"Channel ID: {channel_id}")
            print(f"RSS Feed: {rss_url}")
        
        if args.copy:
            try:
                import subprocess
                if sys.platform == "darwin":
                    subprocess.run(["pbcopy"], input=rss_url, check=True)
                elif sys.platform == "linux":
                    subprocess.run(["xclip", "-selection", "clipboard"], input=rss_url, check=True)
                elif sys.platform == "win32":
                    subprocess.run(["cmd", "/c", "echo", rss_url, "|", "clip"], check=True)
                if not args.quiet:
                    print("\nCopied to clipboard!")
            except Exception as e:
                pass  # Clipboard not available
                
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()