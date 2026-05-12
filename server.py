#!/usr/bin/env python3
"""
YouTube RSS Feed Scanner - Web Server
Serves generated RSS feeds at public URLs for RSS readers to subscribe to.
"""

from flask import Flask, request, Response, redirect, send_from_directory
import rss_scanner
import urllib.parse

app = Flask(__name__, template_folder='templates')


@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')


@app.route('/api/feed', methods=['POST'])
def api_feed():
    """API endpoint for getting feed data."""
    import json
    data = request.get_json()
    
    if not data or 'url' not in data:
        return Response(json.dumps({'error': 'Missing url parameter'}), mimetype='application/json')
    
    url = data['url']
    if not url.startswith('http'):
        url = 'https://' + url
    
    try:
        youtube_rss, channel_id, channel_name, atom_feed, video_count, _ = rss_scanner.get_rss_feed(url)
        
        return Response(json.dumps({
            'youtube_rss': youtube_rss,
            'channel_id': channel_id,
            'channel_name': channel_name,
            'atom_feed': atom_feed,
            'video_count': video_count
        }), mimetype='application/json')
    except Exception as e:
        return Response(json.dumps({'error': str(e)}), mimetype='application/json')


@app.route('/feed/')
@app.route('/feed/<path:channel_url>')
def get_feed(channel_url=None):
    """Generate RSS feed for given channel."""
    if channel_url is None:
        return "Usage: /feed/{youtube_channel_url}"
    
    # Decode URL-encoded parts
    channel_url = urllib.parse.unquote(channel_url)
    
    # Reconstruct full URL (Flask captures everything after /feed/)
    if not channel_url.startswith('http'):
        full_url = f"https://{channel_url}"
    else:
        full_url = channel_url
    
    try:
        _, channel_id, channel_name, atom_feed, video_count, _ = rss_scanner.get_rss_feed(full_url)
        
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)