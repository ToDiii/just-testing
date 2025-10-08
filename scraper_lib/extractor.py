import re
from datetime import datetime
from bs4 import BeautifulSoup

def _find_date(content_area: BeautifulSoup | str) -> str | None:
    """
    Finds a date in a BeautifulSoup tag or a block of text.
    """
    if not content_area:
        return None

    if isinstance(content_area, str):
        text_for_date_search = content_area
    else:
        text_for_date_search = content_area.get_text(separator=' ', strip=True)

    # Limit search area for performance
    text_for_date_search = text_for_date_search[:4000]

    date_patterns = [
        r'(\b\d{1,2}\.\s*\d{1,2}\.\s*\d{2,4}\b)',
        r'(\b\d{4}-\d{1,2}-\d{1,2}\b)',
        r'(\b\d{1,2}-\d{1,2}-\d{2,4}\b)',
        r'(\b\d{1,2}\/\d{1,2}\/\d{2,4}\b)',
        r'(\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember|Jan|Feb|Mrz|Apr|Jun|Jul|Aug|Sep|Okt|Nov|Dez)\.?\s*\d{4})'
    ]

    for pattern in date_patterns:
        match = re.search(pattern, text_for_date_search, re.IGNORECASE)
        if match:
            date_candidate = match.group(1)
            # A more sophisticated date parser could be used here, but for now, returning the string is sufficient.
            return date_candidate

    return None

def extract_data_from_html_page(page_url: str, html_content: str, keywords: list[str], source_municipality_name: str) -> list[dict]:
    """Extracts title, description, date, etc., from an HTML page."""
    soup = BeautifulSoup(html_content, 'html.parser')
    extracted_items = []
    title = ""
    title_selectors_try = [
        'h1.title', 'h2.title', 'h1.headline', 'h2.headline',
        'h1.page-title', 'h2.page-title', 'h1.entry-title',
        'h1[itemprop="headline"]', 'h2[itemprop="headline"]',
        'h1', 'h2'
    ]
    for selector in title_selectors_try:
        tag_name = selector.split('.')[0] if '.' in selector else selector.split('[')[0]
        class_name = selector.split('.')[1] if '.' in selector else None
        if class_name:
            found_title = soup.find(tag_name, class_=re.compile(class_name, re.I))
        elif '[' in selector:
             attr = selector.split('[')[1].split('=')[0]
             val = selector.split('=')[1].split(']')[0].strip('"\'')
             attrs = {attr: re.compile(val, re.I)}
             found_title = soup.find(tag_name, attrs=attrs)
        else:
            found_title = soup.find(tag_name)
        if found_title:
            title = found_title.get_text(strip=True)
            break
    if not title and soup.title:
        title = soup.title.string.strip()

    main_content_selectors = [
        'article.news-article', 'div.news-detail', 'div.news_article', 'div.aktuelles_detail',
        'main#main', 'div#content', 'main.main-content', 'div.main-content',
        'article', 'main', '.content-block', '.text', '.entry-content', '.page-content',
        'div[role="main"]'
    ]
    content_area = None
    for selector in main_content_selectors:
        if '#' in selector:
            tag, elem_id = selector.split('#', 1)
            content_area = soup.find(tag or True, id=elem_id)
        elif '.' in selector:
            if selector.startswith('.'):
                tag_name = 'div'
                class_name = selector[1:]
            else:
                tag_name, class_name = selector.split('.', 1)
            content_area = soup.find(tag_name, class_=re.compile(r'\b' + re.escape(class_name) + r'\b', re.I))
        elif '[' in selector:
            tag_name = selector.split('[')[0]
            try:
                attr_full = selector.split('[')[1].split(']')[0]
                attr_key = attr_full.split('=')[0]
                attr_val = attr_full.split('=')[1].strip('"\'')
                content_area = soup.find(tag_name, {attr_key: re.compile(attr_val, re.I)})
            except IndexError:
                 pass
        else:
            content_area = soup.find(selector)
        if content_area:
            break
    if not content_area:
        content_area = soup.body

    description_snippets = []
    if content_area:
        text_blocks = content_area.find_all(['p', 'div'], limit=30)
        for block in text_blocks:
            if block.name == 'div':
                direct_text = block.find(string=True, recursive=False, strip=True)
                is_texty_div = direct_text and len(direct_text) > 20 and len(block.find_all(True)) < 5
                is_content_class = any(cls in block.get('class', []) for cls in ['text', 'content', 'meldung'])
                if not (is_texty_div or is_content_class):
                    continue
            block_text = block.get_text(separator=' ', strip=True)
            if len(block_text) < 40 and len(block.find_all(['a','strong','b'])) > 0:
                continue
            if not block_text: continue
            for keyword in keywords:
                if keyword in block_text.lower():
                    snippet_max_len = 300
                    snippet = block_text[:snippet_max_len] + ("..." if len(block_text) > snippet_max_len else "")
                    if snippet not in description_snippets:
                         description_snippets.append(snippet)
                    break
            if len(description_snippets) >= 2:
                break
    description = " | ".join(description_snippets)

    publication_date_str = _find_date(content_area)
    if publication_date_str:
        print(f"Found date: {publication_date_str} in {page_url}")

    if title and (description or any(keyword in title.lower() for keyword in keywords)):
        extracted_items.append({
            'title': title,
            'description': description if description else "Keyword found in title, no separate description snippet.",
            'publication_date': publication_date_str if publication_date_str else "Not found",
            'url': page_url,
            'source': source_municipality_name,
            'type': 'HTML Page'
        })
    elif not title and description:
         extracted_items.append({
            'title': f"Notification from {source_municipality_name}",
            'description': description,
            'publication_date': publication_date_str if publication_date_str else "Not found",
            'url': page_url,
            'source': source_municipality_name,
            'type': 'HTML Page'
        })
    return extracted_items

def extract_data_from_pdf_text(pdf_url: str, pdf_text: str, keywords: list[str], source_municipality_name: str) -> list[dict]:
    """Extracts relevant data from the text of a PDF."""
    extracted_items = []
    lines = [line.strip() for line in pdf_text.split('\n') if line.strip()]
    title_candidate = ""
    if lines:
        for i in range(min(5, len(lines))):
            potential_title = lines[i]
            if re.match(r'^(Seite \d+ / \d+|\d{1,2}\s*([./-]\s*\d{1,2}\s*)+|www\.)', potential_title, re.I):
                continue
            if 5 < len(potential_title) < 200:
                title_candidate = potential_title
                if any(keyword in title_candidate.lower() for keyword in keywords + ["bekanntmachung", "amtsblatt", "information", "satzung", "verordnung"]):
                    break
        if not title_candidate and lines:
            title_candidate = lines[0][:150] + "..." if len(lines[0]) > 150 else lines[0]

    description_snippets = []
    text_lower = pdf_text.lower()
    found_keywords_in_pdf_body = False
    for keyword in keywords:
        if keyword in text_lower:
            found_keywords_in_pdf_body = True
            try:
                keyword_pos = text_lower.find(keyword)
                start_pos = max(0, keyword_pos - 150)
                end_pos = min(len(pdf_text), keyword_pos + len(keyword) + 250)
                snippet = pdf_text[start_pos:end_pos].replace('\n', ' ').strip()
                snippet = "..." + re.sub(r'\s+', ' ', snippet) + "..."
                if snippet not in description_snippets:
                    description_snippets.append(snippet)
                if len(description_snippets) >= 1:
                    break
            except Exception: pass
    description = " | ".join(description_snippets)

    publication_date_str = _find_date(pdf_text)
    if publication_date_str:
        print(f"Found date string in PDF '{publication_date_str}' for {pdf_url}")

    if found_keywords_in_pdf_body or any(keyword in title_candidate.lower() for keyword in keywords):
        extracted_items.append({
            'title': title_candidate if title_candidate else "PDF Content (Title not reliably extracted)",
            'description': description if description else "Keyword found in PDF.",
            'publication_date': publication_date_str if publication_date_str else "Not found",
            'url': pdf_url,
            'source': source_municipality_name,
            'type': 'PDF'
        })
    return extracted_items