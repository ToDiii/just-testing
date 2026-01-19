import re

# Selectors for extraction
TITLE_SELECTORS = [
    'h1.title', 'h2.title', 'h1.headline', 'h2.headline',
    'h1.page-title', 'h2.page-title', 'h1.entry-title',
    'h1[itemprop="headline"]', 'h2[itemprop="headline"]',
    'h1', 'h2'
]

CONTENT_SELECTORS = [
    'article.news-article', 'div.news-detail', 'div.news_article', 'div.aktuelles_detail',
    'main#main', 'div#content', 'main.main-content', 'div.main-content',
    'article', 'main', '.content-block', '.text', '.entry-content', '.page-content',
    'div[role="main"]'
]

DATE_PATTERNS = [
    r'(\b\d{1,2}\.\s*\d{1,2}\.\s*\d{2,4}\b)',
    r'(\b\d{4}-\d{1,2}-\d{1,2}\b)',
    r'(\b\d{1,2}-\d{1,2}-\d{2,4}\b)',
    r'(\b\d{1,2}\/\d{1,2}\/\d{2,4}\b)',
    r'(\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember|Jan|Feb|Mrz|Apr|Jun|Jul|Aug|Sep|Okt|Nov|Dez)\.?\s*\d{4})'
]

SKIP_PATTERNS = [
    'impressum', 'datenschutz', 'kontakt', 'sitemap', 'login', 'gallery', 'image', 'logo', 'tel:', 'mailto:'
]

NAV_KEYWORDS = ['aktuelles', 'bekanntmachungen', 'rathaus', 'bauen', 'wirtschaft', 'presse', 'service', 'news', 'mitteilungen']
