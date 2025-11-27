from bs4 import BeautifulSoup
from urllib.parse import urljoin

NAV_KEYWORDS = ['aktuelles', 'bekanntmachungen', 'rathaus', 'bauen', 'wirtschaft', 'presse', 'service', 'news', 'mitteilungen']

def find_relevant_links(html_content: str, base_url: str, keywords: list[str]) -> tuple[list[str], list[str]]:
    """
    Parses HTML to find relevant links based on keywords and PDF extension.
    Returns a tuple of (html_page_links, pdf_links).
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    html_page_links = set()
    pdf_links = set()

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if not href or href.startswith('#') or href.startswith('javascript:'):
            continue

        try:
            absolute_url = urljoin(base_url, href)
        except ValueError:
            continue

        if not (absolute_url.startswith('http://') or absolute_url.startswith('https://')):
            continue

        link_text = a_tag.get_text(separator=' ', strip=True).lower()
        url_path_query = absolute_url.lower().replace(base_url.lower(), '')

        # Check for primary keywords
        if any(keyword in link_text or keyword in url_path_query for keyword in keywords):
            if absolute_url.lower().endswith('.pdf'):
                pdf_links.add(absolute_url)
            else:
                html_page_links.add(absolute_url)
        
        # Check for navigational keywords (only for HTML pages)
        if any(nav in link_text or nav in url_path_query for nav in NAV_KEYWORDS):
            if not absolute_url.lower().endswith('.pdf'):
                # Avoid adding if already added
                if absolute_url not in html_page_links:
                     # Check skip patterns again just in case
                    common_skip_patterns = ['impressum', 'datenschutz', 'kontakt', 'sitemap', 'login', 'gallery', 'image', 'logo', 'tel:', 'mailto:']
                    if not any(skip_word in absolute_url.lower() for skip_word in common_skip_patterns):
                        html_page_links.add(absolute_url)

    return list(html_page_links), list(pdf_links)