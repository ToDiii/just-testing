import requests
import time
import os
import json
import csv

from scraper_lib.fetcher import fetch_html, download_pdf_to_text
from scraper_lib.parser import find_relevant_links
from scraper_lib.extractor import extract_data_from_html_page, extract_data_from_pdf_text

class Scraper:
    def __init__(self, keywords: list[str]):
        if not keywords:
            raise ValueError("Scraper must be initialized with a list of keywords.")
        self.keywords = [k.lower() for k in keywords]
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

        html_links, pdf_links = find_relevant_links(main_page_html, site_url, self.keywords)
        print(f"Found {len(html_links)} relevant HTML links and {len(pdf_links)} PDF links.")

        # Process HTML links
        for i, link_url in enumerate(html_links):
            if i >= max_html_links:
                break
            if link_url in processed_urls:
                continue

            time.sleep(delay)
            page_html = fetch_html(self.session, link_url)
            if page_html:
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

# This file defines the Scraper class, which is now used as a library by the webapp.
# The standalone execution logic has been removed and is now handled by the API endpoints
# in `webapp/routes.py`, which trigger scraping jobs.
pass
