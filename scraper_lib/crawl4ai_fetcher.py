import asyncio
from typing import Optional

import requests as _requests  # alias to avoid collision with function param names


# ---------------------------------------------------------------------------
# Remote server mode  (HTTP POST to an external Crawl4AI server)
# ---------------------------------------------------------------------------

def fetch_html_crawl4ai_remote(url: str, server_url: str) -> Optional[str]:
    """Fetch a URL via an external Crawl4AI server (POST /crawl).

    Raises requests.RequestException on connection/timeout errors so that the
    caller (routes.py) can catch them and trigger the fallback engine.
    """
    endpoint = f"{server_url.rstrip('/')}/crawl"
    payload = {
        "urls": [url],
        "crawler_config": {"page_timeout": 30000},
    }
    resp = _requests.post(endpoint, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    if data.get("success"):
        return data.get("html")
    print(f"Crawl4AI remote: unsuccessful result for {url}: {data.get('error_message')}")
    return None


def fetch_many_crawl4ai_remote(urls: list[str], server_url: str) -> dict[str, Optional[str]]:
    """Fetch multiple URLs via the remote server, one at a time.

    Raises on the first connection-level error (server unreachable).
    Per-URL failures are returned as None values in the result dict.
    """
    results: dict[str, Optional[str]] = {}
    for url in urls:
        try:
            results[url] = fetch_html_crawl4ai_remote(url, server_url)
        except _requests.RequestException:
            # Re-raise connection-level errors so the fallback can kick in
            raise
        except Exception as e:
            print(f"Crawl4AI remote error for {url}: {e}")
            results[url] = None
    return results


async def _fetch_html_async(url: str) -> Optional[str]:
    """Fetch a URL using Crawl4AI's async crawler (supports JavaScript rendering)."""
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        browser_cfg = BrowserConfig(headless=True)
        run_cfg = CrawlerRunConfig(wait_until="networkidle", page_timeout=30000)
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=run_cfg)
            if result.success:
                return result.html
            print(f"Crawl4AI: unsuccessful result for {url}")
            return None
    except Exception as e:
        print(f"Crawl4AI error fetching {url}: {e}")
        return None


async def _fetch_many_async(urls: list[str]) -> dict[str, Optional[str]]:
    """Fetch multiple URLs concurrently using a single Crawl4AI crawler instance."""
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        browser_cfg = BrowserConfig(headless=True)
        run_cfg = CrawlerRunConfig(wait_until="networkidle", page_timeout=30000)
        results: dict[str, Optional[str]] = {}
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            tasks = [crawler.arun(url=url, config=run_cfg) for url in urls]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            for url, resp in zip(urls, responses):
                if isinstance(resp, Exception):
                    print(f"Crawl4AI error fetching {url}: {resp}")
                    results[url] = None
                elif resp.success:
                    results[url] = resp.html
                else:
                    results[url] = None
        return results
    except Exception as e:
        print(f"Crawl4AI batch fetch error: {e}")
        return {url: None for url in urls}


def fetch_html_crawl4ai(url: str) -> Optional[str]:
    """Synchronous wrapper: fetch a single URL with Crawl4AI."""
    return asyncio.run(_fetch_html_async(url))


def fetch_many_crawl4ai(urls: list[str]) -> dict[str, Optional[str]]:
    """Synchronous wrapper: fetch multiple URLs concurrently with Crawl4AI."""
    return asyncio.run(_fetch_many_async(urls))
