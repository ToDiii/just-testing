"""
Crawl4AI-based scraper: drop-in replacement for the requests-based Scraper.

Key advantages over the default engine:
- JavaScript rendering via headless browser (handles dynamic municipality sites)
- Fetches multiple links concurrently within a single browser session
- Returns cleaned HTML that is compatible with the existing parser/extractor pipeline
"""

import time

from scraper import Scraper
from scraper_lib.crawl4ai_fetcher import fetch_html_crawl4ai, fetch_many_crawl4ai
from scraper_lib.fetcher import download_pdf_to_text
from scraper_lib.parser import find_relevant_links, NAV_KEYWORDS
from scraper_lib.extractor import extract_data_from_html_page, extract_data_from_pdf_text


class Crawl4AIScraper:
    """Scraper that uses Crawl4AI for HTML fetching with JS-rendering support.

    The public interface mirrors the original ``Scraper`` class so that it can
    be used as a drop-in replacement in ``routes.py``.

    Logging is intentionally delegated to the ``Scraper`` class methods so that
    both engines share the same in-memory log buffer that the API exposes via
    ``GET /api/scrape/logs``.
    """

    # Delegate all log operations to Scraper so one shared buffer is used
    log = Scraper.log
    get_logs = Scraper.get_logs
    clear_logs = Scraper.clear_logs

    # --- Instance ---

    def __init__(
        self,
        keywords: list[dict],
        max_html_links: int = 15,
        max_pdf_links: int = 10,
        delay: float = 0.5,
    ):
        if not keywords:
            raise ValueError("Scraper must be initialized with a list of keywords.")
        self.keywords = keywords
        self.max_html_links = max_html_links
        self.max_pdf_links = max_pdf_links
        self.delay = delay

    def scrape_site(self, site_name: str, site_url: str) -> list[dict]:
        self.log(f"--- [Crawl4AI] Processing {site_name} ({site_url}) ---")
        all_data: list[dict] = []
        processed_urls: set[str] = set()

        # 1. Fetch the main page with JS rendering
        main_page_html = fetch_html_crawl4ai(site_url)
        if not main_page_html:
            self.log(f"  [ERROR] Could not fetch main page: {site_url}")
            return []

        keyword_strings = [k["word"].lower() for k in self.keywords]
        html_links, pdf_links = find_relevant_links(main_page_html, site_url, keyword_strings)
        self.log(
            f"  Found {len(html_links)} relevant HTML links and {len(pdf_links)} PDF links."
        )

        # 2. Crawl HTML links (batch-fetch for speed, respecting max_html_links)
        i = 0
        while i < len(html_links) and i < self.max_html_links:
            batch_urls = []
            # Build a batch of up to 5 uncrawled links at a time
            while len(batch_urls) < 5 and i < len(html_links) and i < self.max_html_links:
                url = html_links[i]
                i += 1
                if url not in processed_urls:
                    batch_urls.append(url)

            if not batch_urls:
                continue

            self.log(f"  [Crawl4AI] Batch-fetching {len(batch_urls)} HTML pages…")
            pages = fetch_many_crawl4ai(batch_urls)

            for link_url in batch_urls:
                page_html = pages.get(link_url)
                if not page_html:
                    self.log(f"    [SKIP] No content for {link_url}")
                    continue

                # Expand hub pages (news/announcements) like the original scraper
                if any(nav in link_url.lower() for nav in NAV_KEYWORDS):
                    self.log(f"    -> Crawling Hub Page: {link_url}")
                    sub_html_links, sub_pdf_links = find_relevant_links(
                        page_html, link_url, keyword_strings
                    )
                    for sub_link in sub_html_links:
                        if sub_link not in html_links and sub_link not in processed_urls:
                            html_links.append(sub_link)
                    for sub_pdf in sub_pdf_links:
                        if sub_pdf not in pdf_links:
                            pdf_links.append(sub_pdf)

                data = extract_data_from_html_page(link_url, page_html, self.keywords, site_name)
                if data:
                    self.log(f"    [MATCH] Found {len(data)} items on page.")
                all_data.extend(data)
                processed_urls.add(link_url)

            # Polite delay between batches
            time.sleep(self.delay)

        # 3. Crawl PDF links (still uses requests – PDFs don't need a browser)
        import requests

        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }
        )

        for j, pdf_url in enumerate(pdf_links):
            if j >= self.max_pdf_links:
                break
            if pdf_url in processed_urls:
                continue

            time.sleep(self.delay)
            self.log(f"  Scraping PDF: {pdf_url}…")
            pdf_text = download_pdf_to_text(session, pdf_url)
            if pdf_text:
                data = extract_data_from_pdf_text(pdf_url, pdf_text, self.keywords, site_name)
                if data:
                    self.log(f"    [MATCH] Found {len(data)} items in PDF.")
                all_data.extend(data)
                processed_urls.add(pdf_url)

        return all_data
