import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scraper import Scraper


def test_find_relevant_links_separates_html_and_pdf_links():
    html = """
    <html><body>
      <a href='doc1.pdf'>Baugebiet plan PDF</a>
      <a href='/info/bebauungsplan.pdf'>Bebauungsplan</a>
      <a href='/news/baugebiet-update'>Latest Baugebiet news</a>
      <a href='https://other.com/grundstueck-info'>Grundstück Info</a>
      <a href='/kontakt'>Kontakt</a>
    </body></html>
    """
    scraper_instance = Scraper()
    html_links, pdf_links = scraper_instance.find_relevant_links(html, 'https://example.com')

    expected_html = {
        'https://example.com/news/baugebiet-update',
        'https://other.com/grundstueck-info'
    }
    expected_pdfs = {
        'https://example.com/doc1.pdf',
        'https://example.com/info/bebauungsplan.pdf'
    }
    assert set(html_links) == expected_html
    assert set(pdf_links) == expected_pdfs
