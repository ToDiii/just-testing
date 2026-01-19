import re
from datetime import datetime
from bs4 import BeautifulSoup
from .constants import TITLE_SELECTORS, CONTENT_SELECTORS, DATE_PATTERNS

def _find_date(content_area: BeautifulSoup | str) -> str | None:
    """Finds a date in a BeautifulSoup tag or a block of text."""
    if not content_area:
        return None

    text_for_date_search = content_area if isinstance(content_area, str) else content_area.get_text(separator=' ', strip=True)
    text_for_date_search = text_for_date_search[:4000]

    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text_for_date_search, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def extract_data_from_html_page(page_url: str, html_content: str, keywords: list[dict], source_municipality_name: str) -> list[dict]:
    """Extracts title, description, date, etc., from an HTML page."""
    soup = BeautifulSoup(html_content, 'html.parser')
    extracted_items = []
    
    # 1. Title Extraction
    title = ""
    for selector in TITLE_SELECTORS:
        found_title = None
        if '.' in selector:
            tag, cls = selector.split('.', 1)
            found_title = soup.find(tag or True, class_=re.compile(cls, re.I))
        elif '[' in selector:
            tag = selector.split('[')[0]
            attr_full = selector.split('[')[1].split(']')[0]
            key, val = attr_full.split('=')
            found_title = soup.find(tag or True, {key: re.compile(val.strip('"\''), re.I)})
        else:
            found_title = soup.find(selector)
        
        if found_title:
            title = found_title.get_text(strip=True)
            break
    
    if not title and soup.title:
        title = soup.title.string.strip() if soup.title.string else ""

    # 2. Content Area Extraction
    content_area = None
    for selector in CONTENT_SELECTORS:
        if '#' in selector:
            tag, elem_id = selector.split('#', 1)
            content_area = soup.find(tag or True, id=elem_id)
        elif '.' in selector:
            tag = 'div' if selector.startswith('.') else selector.split('.', 1)[0]
            cls = selector[1:] if selector.startswith('.') else selector.split('.', 1)[1]
            content_area = soup.find(tag, class_=re.compile(r'\b' + re.escape(cls) + r'\b', re.I))
        elif '[' in selector:
            tag = selector.split('[')[0]
            try:
                attr_full = selector.split('[')[1].split(']')[0]
                key, val = attr_full.split('=')
                content_area = soup.find(tag or True, {key: re.compile(val.strip('"\''), re.I)})
            except (IndexError, ValueError): pass
        else:
            content_area = soup.find(selector)
        
        if content_area: break
    
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
            for keyword_obj in keywords:
                keyword = keyword_obj['word'].lower()
                if keyword in block_text.lower():
                    snippet_max_len = 300
                    snippet = block_text[:snippet_max_len] + ("..." if len(block_text) > snippet_max_len else "")
                    if snippet not in description_snippets:
                         description_snippets.append(snippet)
                    break
            if len(description_snippets) >= 2:
                break
    description = " | ".join(description_snippets)
    
    # Determine category based on matched keywords in title or description
    matched_category_id = None
    text_to_check = (title + " " + description).lower()
    for keyword_obj in keywords:
        if keyword_obj['word'].lower() in text_to_check:
            matched_category_id = keyword_obj.get('category_id')
            break

    publication_date_str = _find_date(content_area)
    if publication_date_str:
        print(f"Found date: {publication_date_str} in {page_url}")

    if title and (description or any(k['word'].lower() in title.lower() for k in keywords)):
        extracted_items.append({
            'title': title,
            'description': description if description else "Keyword found in title, no separate description snippet.",
            'publication_date': publication_date_str if publication_date_str else "Not found",
            'url': page_url,
            'source': source_municipality_name,
            'type': 'HTML Page',
            'category_id': matched_category_id
        })
    elif not title and description:
         extracted_items.append({
            'title': f"Notification from {source_municipality_name}",
            'description': description,
            'publication_date': publication_date_str if publication_date_str else "Not found",
            'url': page_url,
            'source': source_municipality_name,
            'type': 'HTML Page',
            'category_id': matched_category_id
        })
    return extracted_items

def extract_data_from_pdf_text(pdf_url: str, pdf_text: str, keywords: list[dict], source_municipality_name: str) -> list[dict]:
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
                if any(k['word'].lower() in title_candidate.lower() for k in keywords) or any(x in title_candidate.lower() for x in ["bekanntmachung", "amtsblatt", "information", "satzung", "verordnung"]):
                    break
        if not title_candidate and lines:
            title_candidate = lines[0][:150] + "..." if len(lines[0]) > 150 else lines[0]

    description_snippets = []
    text_lower = pdf_text.lower()
    found_keywords_in_pdf_body = False
    for keyword_obj in keywords:
        keyword = keyword_obj['word'].lower()
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

    # Determine category
    matched_category_id = None
    text_to_check = (title_candidate + " " + description).lower()
    for keyword_obj in keywords:
        if keyword_obj['word'].lower() in text_to_check:
            matched_category_id = keyword_obj.get('category_id')
            break

    publication_date_str = _find_date(pdf_text)
    if publication_date_str:
        print(f"Found date string in PDF '{publication_date_str}' for {pdf_url}")

    if found_keywords_in_pdf_body or any(k['word'].lower() in title_candidate.lower() for k in keywords):
        extracted_items.append({
            'title': title_candidate if title_candidate else "PDF Content (Title not reliably extracted)",
            'description': description if description else "Keyword found in PDF.",
            'publication_date': publication_date_str if publication_date_str else "Not found",
            'url': pdf_url,
            'source': source_municipality_name,
            'type': 'PDF',
            'category_id': matched_category_id
        })
    return extracted_items