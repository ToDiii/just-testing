import requests
import time
import threading
from datetime import datetime

from scraper_lib.fetcher import fetch_html, download_pdf_to_text
from scraper_lib.parser import find_relevant_links
from scraper_lib.extractor import extract_data_from_html_page, extract_data_from_pdf_text

class Scraper:
    _log_buffer = []
    _log_lock = threading.Lock()
    _max_logs = 1000

    @classmethod
    def log(cls, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)
        with cls._log_lock:
            cls._log_buffer.append(formatted_message)
            if len(cls._log_buffer) > cls._max_logs:
                cls._log_buffer.pop(0)

    @classmethod
    def get_logs(cls):
        with cls._log_lock:
            return list(cls._log_buffer)

    @classmethod
    def clear_logs(cls):
        with cls._log_lock:
            cls._log_buffer.clear()

    def __init__(self, keywords: list[dict], max_html_links: int = 15, max_pdf_links: int = 10, delay: float = 0.5):
        if not keywords:
            raise ValueError("Scraper must be initialized with a list of keywords.")
        self.keywords = keywords
        self.max_html_links = max_html_links
        self.max_pdf_links = max_pdf_links
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_site(self, site_name: str, site_url: str) -> list[dict]:
        self.log(f"--- Processing {site_name} ({site_url}) ---")
        all_data = []
        processed_urls = set()

        main_page_html = fetch_html(self.session, site_url)
        if not main_page_html:
            self.log(f"  [ERROR] Could not fetch main page: {site_url}")
            return []

        keyword_strings = [k['word'].lower() for k in self.keywords]
        html_links, pdf_links = find_relevant_links(main_page_html, site_url, keyword_strings)
        self.log(f"Found {len(html_links)} relevant HTML links and {len(pdf_links)} PDF links.")

        i = 0
        while i < len(html_links) and i < self.max_html_links:
            link_url = html_links[i]
            i += 1
            
            if link_url in processed_urls:
                continue

            time.sleep(self.delay)
            self.log(f"  Scraping HTML: {link_url}...")
            page_html = fetch_html(self.session, link_url)
            if page_html:
                from scraper_lib.parser import NAV_KEYWORDS
                if any(nav in link_url.lower() for nav in NAV_KEYWORDS):
                    self.log(f"    -> Crawling Hub Page: {link_url}")
                    sub_html_links, sub_pdf_links = find_relevant_links(page_html, link_url, keyword_strings)
                    
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

        for i, pdf_url in enumerate(pdf_links):
            if i >= self.max_pdf_links:
                break
            if pdf_url in processed_urls:
                continue

            time.sleep(self.delay)
            self.log(f"  Scraping PDF: {pdf_url}...")
            pdf_text = download_pdf_to_text(self.session, pdf_url)
            if pdf_text:
                data = extract_data_from_pdf_text(pdf_url, pdf_text, self.keywords, site_name)
                if data:
                    self.log(f"    [MATCH] Found {len(data)} items in PDF.")
                all_data.extend(data)
                processed_urls.add(pdf_url)

        return all_data