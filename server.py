#!/usr/bin/env python3
"""
YouTube RSS Feed Scanner - Web Server
Serves generated RSS feeds at public URLs for RSS readers to subscribe to.
"""

from flask import Flask, request, Response, redirect
import rss_scanner
import urllib.parse

app = Flask(__name__)


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


@app.route('/')
def index():
    """Home page with usage info."""
    return """<!DOCTYPE html>
<html>
<head><title>YouTube RSS Feed Scanner</title></head>
<body>
<h1>YouTube RSS Feed Scanner</h1>
<p>Subscribe to YouTube channel RSS feeds:</p>
<pre>/feed/{channel_url}</pre>
<p>Examples:</p>
<ul>
<li><a href="/feed/https://www.youtube.com/@Beardmeatsfood">/feed/https://www.youtube.com/@Beardmeatsfood</a></li>
<li><a href="/feed/https://www.youtube.com/@GoogleDevelopers">/feed/https://www.youtube.com/@GoogleDevelopers</a></li>
<li><a href="/feed/https://www.youtube.com/c/MarquesBrownlee">/feed/https://www.youtube.com/c/MarquesBrownlee</a></li>
</ul>
</body>
</html>"""


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)