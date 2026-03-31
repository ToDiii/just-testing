import asyncio
from typing import Optional


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
