#!/usr/bin/env python3
"""Simple terminal RSS reader host.

Fetches an RSS/Atom feed on an interval and prints new entries to the terminal.
"""

from __future__ import annotations

import argparse
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime


def fetch_feed(feed_url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(feed_url, headers={"User-Agent": "TerminalRSSReader/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def parse_entries(xml_bytes: bytes, limit: int) -> list[tuple[str, str, str]]:
    root = ET.fromstring(xml_bytes)

    entries: list[tuple[str, str, str]] = []

    # RSS
    for item in root.findall('.//item'):
        title = (item.findtext('title') or 'Untitled').strip()
        link = (item.findtext('link') or '').strip()
        published = (item.findtext('pubDate') or 'Unknown date').strip()
        entries.append((title, link, published))

    # Atom fallback
    if not entries:
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.findall('.//atom:entry', ns):
            title = (entry.findtext('atom:title', default='Untitled', namespaces=ns) or 'Untitled').strip()
            link_el = entry.find('atom:link', ns)
            link = (link_el.attrib.get('href', '') if link_el is not None else '').strip()
            published = (entry.findtext('atom:published', default='Unknown date', namespaces=ns) or 'Unknown date').strip()
            entries.append((title, link, published))

    return entries[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description='Host a simple RSS reader in your terminal.')
    parser.add_argument('feed_url', help='RSS/Atom feed URL to watch')
    parser.add_argument('--interval', type=int, default=120, help='Seconds between refreshes (default: 120)')
    parser.add_argument('--limit', type=int, default=10, help='Maximum entries to show per refresh (default: 10)')
    args = parser.parse_args()

    seen_links: set[str] = set()

    print(f"\n📡 Terminal Reader started for: {args.feed_url}")
    print(f"⏱ Refresh interval: {args.interval}s | 🧾 Entry limit: {args.limit}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
            try:
                xml_bytes = fetch_feed(args.feed_url)
                entries = parse_entries(xml_bytes, args.limit)
                print(f"\n=== Refresh @ {timestamp} ===")
                if not entries:
                    print('No entries found.')
                for idx, (title, link, published) in enumerate(entries, start=1):
                    marker = '🆕' if link and link not in seen_links else '  '
                    print(f"{idx:02d}. {marker} {title}")
                    print(f"    Date: {published}")
                    if link:
                        print(f"    Link: {link}")
                    if link:
                        seen_links.add(link)
            except Exception as exc:
                print(f"Error fetching/parsing feed: {exc}")

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped terminal reader.")
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
