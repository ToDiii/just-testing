import requests
import time

from scraper_lib.fetcher import fetch_html, download_pdf_to_text
from scraper_lib.parser import find_relevant_links
from scraper_lib.extractor import extract_data_from_html_page, extract_data_from_pdf_text

class Scraper:
    def __init__(self, keywords: list[dict]):
        """
        Initialize Scraper with a list of keywords.
        Each keyword should be a dict with 'word' and optional 'category_id'.
        """
        if not keywords:
            raise ValueError("Scraper must be initialized with a list of keywords.")
        self.keywords = keywords
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def scrape_site(self, site_name: str, site_url: str, max_html_links: int = 15, max_pdf_links: int = 10, delay: float = 0.5) -> list[dict]:
        """
        Scrapes a single site by orchestrating calls to the scraper library modules.
        """
        print(f"--- Processing {site_name} ({site_url}) ---")
        all_data = []
        processed_urls = set()

        main_page_html = fetch_html(self.session, site_url)
        if not main_page_html:
            return []

        keyword_strings = [k['word'].lower() for k in self.keywords]
        html_links, pdf_links = find_relevant_links(main_page_html, site_url, keyword_strings)
        print(f"Found {len(html_links)} relevant HTML links and {len(pdf_links)} PDF links.")

        # Process HTML links
        # Process HTML links
        # We use a while loop to allow adding new links (from hubs) to the list
        i = 0
        while i < len(html_links) and i < max_html_links:
            link_url = html_links[i]
            i += 1
            
            if link_url in processed_urls:
                continue

            time.sleep(delay)
            page_html = fetch_html(self.session, link_url)
            if page_html:
                # Check if this is a "hub" page (navigational)
                # If so, we want to find MORE links on this page
                from scraper_lib.parser import NAV_KEYWORDS
                if any(nav in link_url.lower() for nav in NAV_KEYWORDS):
                    print(f"  -> Crawling Hub Page: {link_url}")
                    sub_html_links, sub_pdf_links = find_relevant_links(page_html, link_url, keyword_strings)
                    
                    # Add new HTML links to the queue if not already present
                    for sub_link in sub_html_links:
                        if sub_link not in html_links and sub_link not in processed_urls:
                            html_links.append(sub_link)
                            
                    # Add new PDF links
                    for sub_pdf in sub_pdf_links:
                        if sub_pdf not in pdf_links:
                            pdf_links.append(sub_pdf)
                
                # Always try to extract data, even from hubs (they might be content pages too)
                data = extract_data_from_html_page(link_url, page_html, self.keywords, site_name)
                all_data.extend(data)
                processed_urls.add(link_url)

        # Process PDF links
        for i, pdf_url in enumerate(pdf_links):
            if i >= max_pdf_links:
                break
            if pdf_url in processed_urls:
                continue

            time.sleep(delay)
            pdf_text = download_pdf_to_text(self.session, pdf_url)
            if pdf_text:
                data = extract_data_from_pdf_text(pdf_url, pdf_text, self.keywords, site_name)
                all_data.extend(data)
                processed_urls.add(pdf_url)

        return all_data