"""
RSS/Atom feed fetcher for scraper_lib.
Parses feed entries and matches against keywords.
"""

from __future__ import annotations
import re
from datetime import datetime
from typing import Optional

try:
    import feedparser
    _FEEDPARSER_OK = True
except ImportError:
    _FEEDPARSER_OK = False


# Heuristics to detect feed URLs
_FEED_PATTERNS = re.compile(
    r'(feed|rss|atom|\.xml|\.rss|/feed$|/rss$|/atom$)',
    re.IGNORECASE,
)


def detect_feed_url(url: str) -> bool:
    """Return True if the URL looks like an RSS/Atom feed."""
    return bool(_FEED_PATTERNS.search(url))


def fetch_feed(url: str, keywords: list[dict], source_name: str) -> list[dict]:
    """
    Parse an RSS/Atom feed and return matching entries as result dicts.

    Parameters
    ----------
    url : str
        Feed URL to parse.
    keywords : list[dict]
        Each dict must have at least a "word" key and optionally "category_id".
    source_name : str
        Human-readable name used as 'source' in the result dicts.

    Returns
    -------
    list[dict] suitable for inserting into the ScrapeResult model.
    """
    if not _FEEDPARSER_OK:
        raise ImportError(
            "feedparser is not installed. Run: pip install feedparser"
        )

    feed = feedparser.parse(url)

    if feed.bozo and not feed.entries:
        raise ValueError(f"Failed to parse feed at {url}: {feed.bozo_exception}")

    kw_list = [k["word"].lower() for k in keywords]
    kw_map = {k["word"].lower(): k.get("category_id") for k in keywords}

    results: list[dict] = []
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        summary = entry.get("summary", "") or ""
        link = entry.get("link", "")

        if not link:
            continue

        combined = (title + " " + summary).lower()

        matched_kw = next(
            (kw for kw in kw_list if kw in combined),
            None,
        )
        if not matched_kw:
            continue

        # Publication date
        pub_date = ""
        if entry.get("published_parsed"):
            try:
                pub_date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
            except Exception:
                pass
        elif entry.get("updated_parsed"):
            try:
                pub_date = datetime(*entry.updated_parsed[:6]).strftime("%Y-%m-%d")
            except Exception:
                pass

        # Strip HTML from summary
        description = re.sub(r'<[^>]+>', ' ', summary).strip()
        description = re.sub(r'\s+', ' ', description)[:500]

        results.append({
            "title": title,
            "description": description,
            "url": link,
            "source": source_name,
            "type": "rss",
            "publication_date": pub_date,
            "category_id": kw_map.get(matched_kw),
        })

    return results
