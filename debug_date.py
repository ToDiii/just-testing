
import sys
import os
import requests
from bs4 import BeautifulSoup

# Add the current directory to the path
sys.path.append(os.getcwd())

from scraper_lib.extractor import _find_date, extract_data_from_html_page

def debug_date(url):
    print(f"Debugging date extraction for: {url}")
    response = requests.get(url)
    html_content = response.text
    
    # Test _find_date directly on the whole content (just to see if regex works)
    print("\n--- Direct Regex Test on first 2000 chars ---")
    date_found = _find_date(html_content[:2000])
    print(f"Date found in raw HTML head: {date_found}")
    
    # Test full extraction
    print("\n--- Full Extraction ---")
    data = extract_data_from_html_page(url, html_content, ["stellenausschreibung"], "Test Source")
    
    if data:
        print(f"Extracted Date: {data[0]['publication_date']}")
        print(f"Extracted Title: {data[0]['title']}")
    else:
        print("No data extracted.")

if __name__ == "__main__":
    url = "https://www.taufkirchen.de/aktuelles/news/stellenausschreibungen-der-gemeinde-taufkirchen-vils"
    if len(sys.argv) > 1:
        url = sys.argv[1]
    debug_date(url)
