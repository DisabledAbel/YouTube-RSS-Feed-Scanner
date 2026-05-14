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
import xml.etree.ElementTree as ET


# Invidious instances to try (open-source YouTube frontends with RSS support)
INVIDIOUS_API_ENDPOINTS = [
    "https://pipedapi.kavin.rocks",
    "https://api.piped.yt",
    "https://api.piped.privacydev.net",
]

# Fallback RSS template (YouTube's native feeds are mostly broken but included as reference)
YOUTUBE_RSS_TEMPLATE = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def _extract_video_ids_from_page(html: str, limit: int = 10) -> list[str]:
    """Extract unique YouTube video IDs from page HTML."""
    video_ids: list[str] = []
    seen_ids: set[str] = set()
    for match in re.finditer(r'"videoId":"([a-zA-Z0-9_-]{11})"', html):
        video_id = match.group(1)
        if video_id not in seen_ids:
            seen_ids.add(video_id)
            video_ids.append(video_id)
        if len(video_ids) >= limit:
            break
    return video_ids


def get_channel_videos(channel_id: str, feed_type: str = "all", limit: int = 10) -> list[dict]:
    """Fetch recent videos from channel pages by scraping."""
    page_path_by_type = {
        "all": "videos",
        "videos": "videos",
        "shorts": "shorts",
        "live": "streams",
    }
    page_path = page_path_by_type.get(feed_type, "videos")

    try:
        page_url = f"https://www.youtube.com/channel/{channel_id}/{page_path}"
        page_html = fetch_url(page_url)
        video_ids = _extract_video_ids_from_page(page_html, limit=limit)
        return [{'videoId': vid, 'title': f'Video {vid}', 'published': ''} for vid in video_ids]
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




def is_valid_channel_id(channel_id: str | None) -> bool:
    return bool(channel_id and re.fullmatch(r"UC[a-zA-Z0-9_-]{22}", channel_id))


def extract_channel_id_from_html(html: str) -> str | None:
    patterns = [
        r'https://www\.youtube\.com/channel/(UC[a-zA-Z0-9_-]{22})',
        r'"externalId":"(UC[a-zA-Z0-9_-]{22})"',
        r'"channelId":"(UC[a-zA-Z0-9_-]{22})"',
        r'"browseId":"(UC[a-zA-Z0-9_-]{22})"',
    ]
    for pattern in patterns:
        m = re.search(pattern, html)
        if m and is_valid_channel_id(m.group(1)):
            return m.group(1)
    return None
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
                    channel_id = extract_channel_id_from_html(html)
                    if channel_id:
                        return channel_id, noembed.get('title', '')
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
                channel_id = extract_channel_id_from_html(html)
                if channel_id:
                    return channel_id, noembed.get('title', '')
        except Exception as e:
            print(f"noembed error: {e}", file=sys.stderr)
        
        # Fallback: direct HTML fetch 
        try:
            html = fetch_url(url)
            channel_id = extract_channel_id_from_html(html)
            if channel_id:
                return channel_id, None
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
            
            channel_id = extract_channel_id_from_html(html)
            if channel_id:
                name_match = re.search(r'"channelName":"([^"]+)"', html)
                channel_name = name_match.group(1) if name_match else None
                return channel_id, channel_name
        except Exception as e:
            print(f"Warning: Failed to fetch {fetch_url_str}: {e}", file=sys.stderr)
            continue
    
    raise ValueError("Could not find channel ID from URL")




def parse_rss_entries(feed_xml: str, limit: int = 10) -> list[dict]:
    """Parse entries from Atom/RSS feed XML."""
    entries: list[dict] = []
    root = ET.fromstring(feed_xml)

    # Atom feed
    if root.tag.endswith('feed'):
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.findall('atom:entry', ns)[:limit]:
            title = (entry.findtext('atom:title', default='Untitled', namespaces=ns) or 'Untitled').strip()
            link = ''
            for link_el in entry.findall('atom:link', ns):
                href = link_el.attrib.get('href', '').strip()
                if href:
                    link = href
                    break
            published = (entry.findtext('atom:published', default='', namespaces=ns)
                         or entry.findtext('atom:updated', default='', namespaces=ns)
                         or '').strip()
            entries.append({'title': title, 'link': link, 'published': published})
        return entries

    # RSS 2.0 feed
    channel = root.find('channel')
    if channel is not None:
        for item in channel.findall('item')[:limit]:
            title = (item.findtext('title') or 'Untitled').strip()
            link = (item.findtext('link') or '').strip()
            published = (item.findtext('pubDate') or '').strip()
            entries.append({'title': title, 'link': link, 'published': published})

    return entries


def read_feed(feed_url: str, limit: int = 10) -> list[dict]:
    """Fetch and parse a feed URL."""
    xml = fetch_url(feed_url)
    return parse_rss_entries(xml, limit=limit)

def get_rss_feed(url: str, include_api_endpoints: bool = False, base_url: str = "http://localhost:8080", feed_type: str = "all") -> tuple:
    """Get RSS feed data for a YouTube channel.
    
    Returns: (youtube_rss, channel_id, channel_name, atom_feed, video_count, invidious_rss, api_endpoints)
    """
    channel_id, channel_name = extract_channel_id(url)
    
    # YouTube's native RSS URL (mostly broken but included for reference)
    youtube_rss = YOUTUBE_RSS_TEMPLATE.format(channel_id=channel_id)
    
    # Try to get videos from the selected YouTube channel page
    videos = get_channel_videos(channel_id, feed_type=feed_type)
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
            "atom_feed_path": f"{base_url.rstrip('/')}/feed/all/{encoded_url}",
            "atom_feed_query": f"{base_url.rstrip('/')}/feed/all/{urllib.parse.quote(url, safe="")}",
            "videos_feed": f"{base_url.rstrip('/')}/feed/videos/{encoded_url}",
            "shorts_feed": f"{base_url.rstrip('/')}/feed/shorts/{encoded_url}",
            "live_feed": f"{base_url.rstrip('/')}/feed/live/{encoded_url}",
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
    parser.add_argument("--read", action="store_true", help="Read and display recent entries from discovered RSS feed")
    parser.add_argument("--limit", type=int, default=10, help="Number of feed entries to show with --read (default: 10)")
    
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

        if args.read:
            feed_source = invidious_rss or youtube_rss
            print(f"\nReading feed: {feed_source}")
            entries = read_feed(feed_source, limit=max(1, args.limit))
            if not entries:
                print("No entries found in feed.")
            for idx, entry in enumerate(entries, start=1):
                print(f"\n{idx}. {entry['title']}")
                if entry['published']:
                    print(f"   Published: {entry['published']}")
                if entry['link']:
                    print(f"   Link: {entry['link']}")

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
