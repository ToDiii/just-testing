from bs4 import BeautifulSoup
from urllib.parse import urljoin

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

        if any(keyword in link_text or keyword in url_path_query for keyword in keywords):
            if absolute_url.lower().endswith('.pdf'):
                pdf_links.add(absolute_url)
            else:
                common_skip_patterns = ['impressum', 'datenschutz', 'kontakt', 'sitemap', 'login', 'gallery', 'image', 'logo', 'tel:', 'mailto:']
                if not any(skip_word in absolute_url.lower() for skip_word in common_skip_patterns) or any(keyword in url_path_query for keyword in keywords):
                    html_page_links.add(absolute_url)

    return list(html_page_links), list(pdf_links)
