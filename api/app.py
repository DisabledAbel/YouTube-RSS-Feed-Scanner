#!/usr/bin/env python3
"""
YouTube RSS Feed Scanner - Web Server
Serves generated RSS feeds at public URLs for RSS readers to subscribe to.
"""

from flask import Flask, request, Response, send_from_directory, jsonify
from flask_caching import Cache
import rss_scanner
import urllib.parse
import urllib.request
import urllib.error
import json

app = Flask(__name__, template_folder='api')
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300})


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/feed', methods=['GET', 'POST'])
def api_feed():
    """API endpoint for getting feed data."""
    # Try query parameters first, then fall back to JSON body
    url = request.args.get('url')
    data = request.get_json(silent=True) or {}

    if not url:
        if not data or 'url' not in data:
            return jsonify({
                'error': 'Missing url parameter',
                'usage': {
                    'post_json': {'url': 'https://www.youtube.com/@channel', 'include_api_endpoints': False},
                    'get_query': '/api/feed?url=https://www.youtube.com/@channel'
                }
            }), 400
        url = data['url']
    else:
        # Merge query args with JSON body if present
        if not isinstance(data, dict):
            data = {}
    if not url:
        return jsonify({'error': 'Missing url parameter'}), 400
    if not url.startswith('http'):
        url = 'https://' + url
    
    try:
        # Normalize include_api_endpoints to boolean
        raw_value = data.get('include_api_endpoints', False)
        feed_type = str(data.get('feed_type', request.args.get('feed_type', 'all'))).lower().strip()
        if feed_type not in ('all', 'videos', 'shorts', 'live'):
            return jsonify({'error': 'Invalid feed_type. Use all, videos, shorts, or live.'}), 400
        if isinstance(raw_value, bool):
            include_api_endpoints = raw_value
        elif isinstance(raw_value, str):
            include_api_endpoints = raw_value.lower() in ('true', '1', 'yes')
        elif isinstance(raw_value, (int, float)):
            include_api_endpoints = raw_value == 1
        else:
            include_api_endpoints = False

        base_url = request.host_url.rstrip('/')
        youtube_rss, channel_id, channel_name, atom_feed, video_count, _, api_endpoints = rss_scanner.get_rss_feed(
            url,
            include_api_endpoints=include_api_endpoints,
            base_url=base_url,
            feed_type=feed_type
        )

        encoded_url = urllib.parse.quote(url, safe="")
        selected_feed_path = f"/feed/{feed_type}/{encoded_url}"
        selected_feed = f"{base_url}{selected_feed_path}"

        discord_result = None
        discord_webhook_url = data.get('discord_webhook_url', '').strip()
        if discord_webhook_url:
            discord_result = send_to_discord(
                webhook_url=discord_webhook_url,
                youtube_rss=youtube_rss,
                channel_id=channel_id,
                channel_name=channel_name,
                video_count=video_count,
                api_endpoints=api_endpoints
            )
        
        return Response(json.dumps({
            'youtube_rss': youtube_rss,
            'selected_feed': selected_feed,
            'selected_feed_path': selected_feed_path,
            'feed_type': feed_type,
            'channel_id': channel_id,
            'channel_name': channel_name,
            'atom_feed': atom_feed,
            'video_count': video_count,
            'api_endpoints': api_endpoints,
            'discord': discord_result
        }), mimetype='application/json')
    except Exception as e:
        return Response(json.dumps({'error': str(e)}), mimetype='application/json', status=500)


def send_to_discord(webhook_url: str, youtube_rss: str, channel_id: str | None, channel_name: str | None, video_count: int, api_endpoints: dict | None):
    """Send feed details to a Discord webhook if configured."""
    if not webhook_url.startswith('https://discord.com/api/webhooks/'):
        return {'ok': False, 'error': 'Invalid Discord webhook URL format'}

    display_name = channel_name or channel_id or 'Unknown Channel'
    lines = [
        f"**Channel:** {display_name}",
        f"**Channel ID:** `{channel_id or 'unknown'}`",
        f"**Videos Found:** {video_count}",
        f"**YouTube RSS:** {youtube_rss}"
    ]

    if api_endpoints and api_endpoints.get('json_api'):
        lines.append(f"**JSON API:** {api_endpoints['json_api']}")

    payload = {
        "username": "YouTube RSS Scanner",
        "content": "🔔 New YouTube RSS feed connection configured\n" + "\n".join(lines)
    }

    req = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.status
        if 200 <= status < 300:
            return {'ok': True, 'status': status}
        return {'ok': False, 'status': status}
    except urllib.error.HTTPError as e:
        app.logger.exception('Discord webhook HTTP error')
        return {'ok': False, 'error': 'webhook request failed', 'status': e.code}
    except urllib.error.URLError as e:
        app.logger.exception('Discord webhook URL error')
        return {'ok': False, 'error': 'webhook request failed'}


@app.route('/feed/')
def feed_usage():
    return "Usage: /feed/{type}/{youtube_channel_url} where type is all|videos|shorts|live"


@app.route('/feed/<feed_type>/<path:channel_url>')
def get_feed(feed_type, channel_url=None):
    """Generate RSS feed for given channel."""
    if channel_url is None:
        return "Usage: /feed/{type}/{youtube_channel_url}"

    if feed_type not in ("all", "videos", "shorts", "live"):
        return Response("Invalid feed type", status=400)
    
    # Decode URL-encoded parts
    channel_url = urllib.parse.unquote(channel_url)
    
    # Reconstruct full URL (Flask captures everything after /feed/)
    if not channel_url.startswith('http'):
        full_url = f"https://{channel_url}"
    else:
        full_url = channel_url
    
    try:
        _, channel_id, channel_name, atom_feed, video_count, _, _ = rss_scanner.get_rss_feed(full_url, feed_type=feed_type)
        
        if atom_feed:
            # Fix channel name in feed
            if channel_name:
                atom_feed = atom_feed.replace(
                    f">{channel_id or channel_id} - YouTube Videos",
                    f">{channel_name} - YouTube Videos"
                )
                atom_feed = atom_feed.replace(
                    f"<name>{channel_id or channel_id}</name>",
                    f"<name>{channel_name}</name>"
                )
            return Response(atom_feed, mimetype='application/xml')
        else:
            return Response("No videos found", status=404)
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)


@app.route('/feed/<feed_type>/<path:channel>', methods=['GET'])
@cache.cached(timeout=300, key_prefix=lambda: f"feed_{request.path}")
def get_cached_feed(feed_type, channel):
    """Cached RSS feed endpoint - updates every 5 minutes."""
    if feed_type not in ("all", "videos", "shorts", "live"):
        return Response("Invalid feed type", status=400)

    # Clean channel from URL
    channel = urllib.parse.unquote(channel)
    if channel.startswith('http'):
        full_url = channel
    else:
        full_url = f"https://{channel}"
    
    try:
        _, channel_id, channel_name, atom_feed, video_count, _, _ = rss_scanner.get_rss_feed(full_url, feed_type=feed_type)
        
        if atom_feed:
            if channel_name:
                atom_feed = atom_feed.replace(
                    f">{channel_id or channel_id} - YouTube Videos",
                    f">{channel_name} - YouTube Videos"
                )
                atom_feed = atom_feed.replace(
                    f"<name>{channel_id or channel_id}</name>",
                    f"<name>{channel_name}</name>"
                )
            return Response(atom_feed, mimetype='application/xml')
        else:
            return Response("No videos found", status=404)
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
