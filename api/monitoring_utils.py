import time
import urllib.request
import urllib.error
import urllib.parse
import socket
import ipaddress
import defusedxml.ElementTree as ET
from datetime import datetime, timezone

def is_safe_url(url):
    """
    Validate URL to prevent SSRF.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False

        hostname = parsed.hostname
        if not hostname:
            return False

        # Resolve hostname to IPs
        addr_info = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip = ipaddress.ip_address(ip_str)

            if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast:
                return False
            if hasattr(ip, 'is_global') and not ip.is_global:
                return False

        return True
    except Exception:
        return False

def parse_xml(content_bytes):
    """
    Parse XML content and extract feed info.
    Returns: { 'title': str, 'updated': str, 'items': [ { 'title': str, 'pubDate': str, 'updated': str } ] } or None
    """
    if not content_bytes:
        return None
    try:
        root = ET.fromstring(content_bytes)

        # Atom feed
        if root.tag.endswith('feed'):
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            items = []
            for entry in root.findall('atom:entry', ns):
                items.append({
                    'title': entry.findtext('atom:title', namespaces=ns),
                    'updated': entry.findtext('atom:updated', namespaces=ns),
                    'pubDate': entry.findtext('atom:published', namespaces=ns)
                })
            return {
                'title': root.findtext('atom:title', namespaces=ns),
                'updated': root.findtext('atom:updated', namespaces=ns),
                'items': items
            }

        # RSS 2.0
        channel = root.find('channel')
        if channel is not None:
            items = []
            for item in channel.findall('item'):
                items.append({
                    'title': item.findtext('title'),
                    'pubDate': item.findtext('pubDate'),
                    'updated': None
                })
            return {
                'title': channel.findtext('title'),
                'updated': channel.findtext('lastBuildDate') or channel.findtext('pubDate'),
                'items': items
            }
    except Exception:
        return None
    return None

def get_latest_timestamp(parsed_feed):
    """
    Detect the latest update timestamp from parsed feed.
    """
    if not parsed_feed:
        return None

    dates = []

    def try_parse_date(date_str):
        if not date_str:
            return None
        # Try various formats
        formats = [
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%Y-%m-%d %H:%M:%S'
        ]
        for fmt in formats:
            try:
                # Handle 'Z' suffix
                if date_str.endswith('Z'):
                    date_str = date_str.replace('Z', '+00:00')
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    if parsed_feed.get('updated'):
        dt = try_parse_date(parsed_feed['updated'])
        if dt:
            dates.append(dt)

    for item in parsed_feed.get('items', []):
        for key in ['updated', 'pubDate']:
            if item.get(key):
                dt = try_parse_date(item[key])
                if dt:
                    dates.append(dt)

    if not dates:
        return None

    # Ensure all datetimes are timezone-aware for comparison
    aware_dates = []
    for d in dates:
        if d.tzinfo is None:
            aware_dates.append(d.replace(tzinfo=timezone.utc))
        else:
            aware_dates.append(d)

    latest = max(aware_dates)
    return latest.isoformat()

def get_relative_time(iso_timestamp):
    """
    Convert ISO timestamp to human-readable relative time.
    """
    if not iso_timestamp:
        return None
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        now = datetime.now(timezone.utc)
        diff = now - dt

        seconds = int(diff.total_seconds())
        if seconds < 0:
            return "in the future"
        if seconds < 60:
            return f"{seconds} seconds ago"

        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes} {'minute' if minutes == 1 else 'minutes'} ago"

        hours = minutes // 60
        if hours < 24:
            return f"{hours} {'hour' if hours == 1 else 'hours'} ago"

        days = hours // 24
        if days < 30:
            return f"{days} {'day' if days == 1 else 'days'} ago"

        months = days // 30
        if months < 12:
            return f"{months} {'month' if months == 1 else 'months'} ago"

        years = max(1, days // 365)
        return f"{years} {'year' if years == 1 else 'years'} ago"
    except Exception:
        return None

def calculate_health_and_score(fetch_result, parsed_feed, latest_timestamp):
    """
    Calculate health status, reason, and score.
    Returns: (status, reason, score)
    """
    content, response_time, fetch_error, status_code = fetch_result

    # 0. Base health and score
    status = "healthy"
    reason = None
    score = 100

    # 1. Check fetch errors
    if fetch_error:
        score = 0
        status = "broken"
        reason = fetch_error
        return status, reason, score

    # 2. Check parsing success
    if not parsed_feed:
        score = 0
        status = "broken"
        reason = "Invalid XML"
        return status, reason, score

    # 3. Check item count
    items = parsed_feed.get('items', [])
    if not items:
        score = 40
        status = "broken"
        reason = "Empty feed"
        return status, reason, score

    # 4. Response time penalties
    if response_time > 2000:
        score -= 10
    if response_time > 5000:
        score -= 20
        status = "warning"
        reason = "Slow response"

    # 5. Recent uploads check (stale feed detection)
    if latest_timestamp:
        dt = datetime.fromisoformat(latest_timestamp)
        now = datetime.now(timezone.utc)
        days_ago = (now - dt).days
        if days_ago > 30:
            score -= 30
            if status == "healthy":
                status = "warning"
                reason = "Feed has no recent uploads"
    else:
        score -= 10
        if status == "healthy":
            status = "warning"
            reason = "No timestamps found"

    # Ensure score is within 0-100
    score = max(0, min(100, score))

    return status, reason, score

def fetch_feed(url, timeout=10):
    """
    Fetch URL content and measure response time.
    Returns: (content_bytes, response_time_ms, error_reason, status_code)
    """
    start_time = time.time()

    if not is_safe_url(url):
        return None, 0, "Disallowed URL", None

    headers = {
        'User-Agent': 'YouTube RSS Monitor/1.0',
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            content = response.read()
            duration = int((time.time() - start_time) * 1000)
            return content, duration, None, response.status
    except urllib.error.HTTPError as e:
        duration = int((time.time() - start_time) * 1000)
        return None, duration, f"HTTP {e.code}", e.code
    except urllib.error.URLError as e:
        duration = int((time.time() - start_time) * 1000)
        reason = str(e.reason)
        if isinstance(e.reason, socket.timeout):
            reason = "request timeout"
        return None, duration, reason, None
    except socket.timeout:
        duration = int((time.time() - start_time) * 1000)
        return None, duration, "request timeout", None
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        return None, duration, str(e), None
