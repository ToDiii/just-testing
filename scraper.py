import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from datetime import datetime
import io
from PyPDF2 import PdfReader # Ensure this matches the library you have / expect
import json
import csv
import time # For polite scraping

# Global list of keywords (lowercase for case-insensitive matching)
KEYWORDS = ["baugebiet", "bebauungsplan", "flächennutzungsplan", "grundstück", "bauplatz", "bauland", "ausschreibung", "verkauf", "entwicklung", "neubaugebiet", "sanierung"]

# --- Network Function ---
def fetch_html(url):
    """Fetches HTML content from a URL."""
    print(f"Fetching: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=20) # Increased timeout
        response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# --- Link Discovery Function ---
def find_relevant_links(html_content, base_url):
    """Parses HTML to find relevant links based on keywords and PDF extension."""
    soup = BeautifulSoup(html_content, 'html.parser')
    html_page_links = set()
    pdf_links = set()

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if not href or href.startswith('#') or href.startswith('javascript:'): # Skip empty, anchor or javascript links
            continue

        try:
            absolute_url = urljoin(base_url, href)
        except ValueError:
            continue

        if not (absolute_url.startswith('http://') or absolute_url.startswith('https://')):
            continue

        link_text = a_tag.get_text(separator=' ', strip=True).lower()
        found_keyword = False
        url_path_query = absolute_url.lower().replace(base_url.lower(), '')
        for keyword in KEYWORDS:
            if keyword in link_text or keyword in url_path_query:
                found_keyword = True
                break
        
        if found_keyword:
            if absolute_url.lower().endswith('.pdf'):
                pdf_links.add(absolute_url)
            else:
                common_skip_patterns = ['impressum', 'datenschutz', 'kontakt', 'sitemap', 'login', 'gallery', 'image', 'logo', 'tel:', 'mailto:']
                is_common_skip_link = any(skip_word in absolute_url.lower() for skip_word in common_skip_patterns)
                if not is_common_skip_link or any(keyword in url_path_query for keyword in KEYWORDS):
                     html_page_links.add(absolute_url)

    return list(html_page_links), list(pdf_links)

# --- HTML Content Extraction Function ---
def extract_data_from_html_page(page_url, html_content, source_municipality_name):
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
            # split at '#' to handle selectors like 'div#main'
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
        else: # Tag
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
            for keyword in KEYWORDS:
                if keyword in block_text.lower():
                    snippet_max_len = 300
                    snippet = block_text[:snippet_max_len] + ("..." if len(block_text) > snippet_max_len else "")
                    if snippet not in description_snippets:
                         description_snippets.append(snippet)
                    break 
            if len(description_snippets) >= 2:
                break
    description = " | ".join(description_snippets)
    
    publication_date_str = None
    if content_area:
        text_for_date_search = content_area.get_text(separator=' ', strip=True)[:3000]
        date_patterns = [
            r'(\b\d{1,2}\s*\.\s*\d{1,2}\s*\.\s*\d{2,4}\b)', 
            r'(\b\d{4}\s*-\s*\d{1,2}\s*-\s*\d{1,2}\b)',   
            r'(\b\d{1,2}\s*-\s*\d{1,2}\s*-\s*\d{2,4}\b)', 
            r'(\b\d{1,2}\s*\/\s*\d{1,2}\s*\/\s*\d{2,4}\b)',
            r'(\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember|Jan|Feb|Mrz|Apr|Jun|Jul|Aug|Sep|Okt|Nov|Dez)\.?\s*\d{2,4})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text_for_date_search, re.IGNORECASE)
            if match:
                date_candidate = match.group(1)
                formats_to_try = [
                    "%d.%m.%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", 
                    "%d.%m.%y", "%d-%m-%y", "%d/%m/%y",
                    "%d. %B %Y", "%d. %b %Y"
                ]
                try:
                    gs_months = {'januar': '01', 'februar': '02', 'märz': '03', 'april': '04', 'mai': '05', 'juni': '06', 
                                'juli': '07', 'august': '08', 'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12',
                                'jan': '01', 'feb': '02', 'mrz': '03', 'apr': '04', 'jun': '06', 'jul': '07', 
                                'aug': '08', 'sep': '09', 'okt': '10', 'nov': '11', 'dez': '12'}
                    temp_date_candidate = date_candidate.lower()
                    for m_de, m_num in gs_months.items():
                        temp_date_candidate = temp_date_candidate.replace(m_de, m_num)
                    parsed_date = None
                    for fmt in formats_to_try:
                        try:
                            candidate_for_fmt = temp_date_candidate
                            if "%B" in fmt or "%b" in fmt:
                                candidate_for_fmt = date_candidate
                            else:
                                candidate_for_fmt = temp_date_candidate.replace(".","").replace(" ","").replace("/","").replace("-","")
                                if "%d%m%Y" not in fmt.replace(".","").replace(" ","").replace("/","").replace("-",""):
                                     candidate_for_fmt = temp_date_candidate
                            parsed_date = datetime.strptime(candidate_for_fmt, fmt.replace(" ",""))
                            if parsed_date: break
                        except ValueError:
                             try: 
                                parsed_date = datetime.strptime(date_candidate, fmt)
                                if parsed_date: break
                             except ValueError:
                                continue
                    if parsed_date:
                        publication_date_str = parsed_date.strftime('%Y-%m-%d')
                        break 
                except Exception: 
                    pass 
        if publication_date_str:
            print(f"Found date: {publication_date_str} in {page_url}")

    if title and (description or any(keyword in title.lower() for keyword in KEYWORDS)):
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

def download_pdf_to_text(pdf_url):
    print(f"Downloading PDF: {pdf_url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(pdf_url, headers=headers, timeout=45) 
        response.raise_for_status()
        pdf_file_like_object = io.BytesIO(response.content)
        text = ""
        try:
            reader = PdfReader(pdf_file_like_object)
            if reader.is_encrypted:
                print(f"PDF {pdf_url} is encrypted. Attempting to decrypt with empty password.")
                try:
                    reader.decrypt('')
                except Exception as e_decrypt:
                    print(f"Failed to decrypt {pdf_url}: {e_decrypt}. Skipping.")
                    return None
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n" 
        except Exception as e:
            print(f"PyPDF2 error while reading {pdf_url}: {e}. PDF might be corrupted or unreadable.")
            return None 
        if not text.strip():
             print(f"Warning: No text extracted from PDF (possibly image-based or empty): {pdf_url}")
             return None 
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF {pdf_url}: {e}")
        return None
    except Exception as e: 
        print(f"Unexpected error processing PDF {pdf_url}: {e}")
        return None

def extract_data_from_pdf_text(pdf_url, pdf_text, source_municipality_name):
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
                if any(keyword in title_candidate.lower() for keyword in KEYWORDS + ["bekanntmachung", "amtsblatt", "information", "satzung", "verordnung"]):
                    break 
        if not title_candidate and lines:
            title_candidate = lines[0][:150] + "..." if len(lines[0]) > 150 else lines[0]
    
    description_snippets = []
    text_lower = pdf_text.lower()
    found_keywords_in_pdf_body = False
    for keyword in KEYWORDS:
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

    publication_date_str = None
    text_sample_for_date = pdf_text[:2000] + "\n" + pdf_text[-2000:]
    date_patterns = [
        r'(\b\d{1,2}\s*[\.\/-]\s*\d{1,2}\s*[\.\/-]\s*\d{2,4}\b)',
        r'(\b\d{4}\s*[\.\/-]\s*\d{1,2}\s*[\.\/-]\s*\d{1,2}\b)',
        r'(\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember|Jan\.|Feb\.|Mrz\.|Apr\.|Jun\.|Jul\.|Aug\.|Sep\.|Okt\.|Nov\.|Dez\.)\s*\d{2,4})'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text_sample_for_date, re.IGNORECASE)
        if match:
            date_candidate = match.group(1)
            publication_date_str = date_candidate
            print(f"Found date string in PDF '{publication_date_str}' for {pdf_url}")
            break 

    if found_keywords_in_pdf_body and (title_candidate or description):
        extracted_items.append({
            'title': title_candidate if title_candidate else "PDF Content (Title not reliably extracted)",
            'description': description if description else "Keyword found in PDF, no specific snippet extracted.",
            'publication_date': publication_date_str if publication_date_str else "Not found", 
            'url': pdf_url,
            'source': source_municipality_name,
            'type': 'PDF'
        })
    elif any(keyword in title_candidate.lower() for keyword in KEYWORDS) and title_candidate:
         extracted_items.append({
            'title': title_candidate,
            'description': description if description else "Keyword found in PDF title. No other text snippet.",
            'publication_date': publication_date_str if publication_date_str else "Not found",
            'url': pdf_url,
            'source': source_municipality_name,
            'type': 'PDF'
        })
    return extracted_items

def save_data(data, json_filepath="extracted_data.json", csv_filepath="extracted_data.csv"):
    if not data:
        print("No data to save.")
        return
    print(f"Saving data to {json_filepath} and {csv_filepath}...")
    try:
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved {len(data)} items to {json_filepath}")
    except IOError as e:
        print(f"Error saving data to JSON file {json_filepath}: {e}")
    try:
        if data:
            all_keys = set()
            for row in data:
                all_keys.update(row.keys())
            defaulted_data = []
            for row in data:
                defaulted_row = {key: row.get(key, "N/A") for key in all_keys}
                defaulted_data.append(defaulted_row)
            if not defaulted_data:
                print("No data to write to CSV after defaulting.")
                return
            headers = list(all_keys)
            with open(csv_filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore') 
                writer.writeheader()
                writer.writerows(defaulted_data) 
            print(f"Successfully saved {len(defaulted_data)} items to {csv_filepath}")
    except IOError as e:
        print(f"Error saving data to CSV file {csv_filepath}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during CSV saving: {e}")

if __name__ == "__main__":
    TARGET_SITES = {
        "VG Velden": "https://www.vg-velden.de/",
        "Markt Velden": "https://www.markt-velden.de/",
        "VG Wartenberg": "https://www.vg-wartenberg.de/", 
        "Markt Wartenberg": "https://www.vg-wartenberg.de/wartenberg/", 
        "Bodenkirchen": "https://www.bodenkirchen.de/",
        "Buchbach": "https://www.buchbach.de/", 
        "Dorfen": "https://www.dorfen.de/", 
        "Geisenhausen": "https://www.geisenhausen.de/", 
        "Taufkirchen (Vils)": "https://www.taufkirchen.de/", 
        "Vilsbiburg": "https://www.vilsbiburg.de/" 
    }
    all_extracted_data = []
    processed_urls = set() 
    MAX_HTML_LINKS_PER_SITE = 15
    MAX_PDF_LINKS_PER_SITE = 10
    POLITENESS_DELAY_SECONDS = 0.5
    json_output_file = "extracted_data.json"
    csv_output_file = "extracted_data.csv"

    for site_name, site_url in TARGET_SITES.items():
        print(f"--- Processing {site_name} ({site_url}) ---")
        main_page_html = fetch_html(site_url)
        if main_page_html:
            html_links, pdf_links = find_relevant_links(main_page_html, site_url)
            print(f"Found {len(html_links)} relevant HTML page link(s) and {len(pdf_links)} PDF link(s) on {site_name} main page.")
            html_processed_count = 0
            for link_url in html_links:
                if html_processed_count >= MAX_HTML_LINKS_PER_SITE:
                    print(f"Reached max HTML links ({MAX_HTML_LINKS_PER_SITE}) for {site_name}.")
                    break
                if link_url in processed_urls:
                    continue 
                print(f"Politely waiting for {POLITENESS_DELAY_SECONDS}s before next HTML fetch...")
                time.sleep(POLITENESS_DELAY_SECONDS)
                page_html = fetch_html(link_url)
                if page_html:
                    data_from_page = extract_data_from_html_page(link_url, page_html, site_name)
                    if data_from_page:
                        all_extracted_data.extend(data_from_page)
                        print(f"Extracted {len(data_from_page)} item(s) from HTML: {link_url.split('?')[0]}...") 
                    processed_urls.add(link_url)
                    html_processed_count += 1
            
            pdf_processed_count = 0
            for pdf_url in pdf_links:
                if pdf_processed_count >= MAX_PDF_LINKS_PER_SITE:
                    print(f"Reached max PDF links ({MAX_PDF_LINKS_PER_SITE}) for {site_name}.")
                    break
                if pdf_url in processed_urls:
                    continue
                print(f"Politely waiting for {POLITENESS_DELAY_SECONDS}s before next PDF download...")
                time.sleep(POLITENESS_DELAY_SECONDS) 
                pdf_text_content = download_pdf_to_text(pdf_url)
                if pdf_text_content:
                    data_from_pdf = extract_data_from_pdf_text(pdf_url, pdf_text_content, site_name)
                    if data_from_pdf:
                        all_extracted_data.extend(data_from_pdf)
                        print(f"Extracted {len(data_from_pdf)} item(s) from PDF: {pdf_url.split('?')[0]}...") 
                processed_urls.add(pdf_url)
                pdf_processed_count += 1
        print(f"--- Finished processing {site_name}. Total items collected so far: {len(all_extracted_data)} ---")

    print(f"\n--- Total {len(all_extracted_data)} items extracted from all sites ---")
    if all_extracted_data:
        save_data(all_extracted_data, json_filepath=json_output_file, csv_filepath=csv_output_file) 
        print("\n--- Summary of First Few Extracted Data Items (max 5) ---")
        for i, item in enumerate(all_extracted_data[:5]): 
            print(f"Item {i+1}:")
            print(f"  Title: {item.get('title')}")
            print(f"  Desc: {item.get('description', '')[:100]}...")
            print(f"  Date: {item.get('publication_date')}")
            print(f"  URL: {item.get('url')}")
            print(f"  Source: {item.get('source')}")
            print(f"  Type: {item.get('type')}")
            print("  ---")
        if len(all_extracted_data) > 5:
            print(f"... and {len(all_extracted_data) - 5} more items (not printed in summary).")
    else:
        print("No data extracted from any sources during this run.")
    print(f"\nScript finished. Check '{json_output_file}' and '{csv_output_file}' for results.")
