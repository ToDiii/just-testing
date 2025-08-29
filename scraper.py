import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
from datetime import datetime
import io
import os
import tempfile
from pdf2image import convert_from_path
import pytesseract
from PyPDF2 import PdfReader
import json
import csv
import time

class Scraper:
    def __init__(self, keywords):
        if not keywords:
            raise ValueError("Scraper must be initialized with a list of keywords.")
        self.keywords = [k.lower() for k in keywords]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch_html(self, url):
        """Fetches HTML content from a URL."""
        print(f"Fetching: {url}")
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def find_relevant_links(self, html_content, base_url):
        """Parses HTML to find relevant links based on keywords and PDF extension."""
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

            if any(keyword in link_text or keyword in url_path_query for keyword in self.keywords):
                if absolute_url.lower().endswith('.pdf'):
                    pdf_links.add(absolute_url)
                else:
                    common_skip_patterns = ['impressum', 'datenschutz', 'kontakt', 'sitemap', 'login', 'gallery', 'image', 'logo', 'tel:', 'mailto:']
                    if not any(skip_word in absolute_url.lower() for skip_word in common_skip_patterns) or any(keyword in url_path_query for keyword in self.keywords):
                        html_page_links.add(absolute_url)

        return list(html_page_links), list(pdf_links)

    def extract_data_from_html_page(self, page_url, html_content, source_municipality_name):
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
                for keyword in self.keywords:
                    if keyword in block_text.lower():
                        snippet_max_len = 300
                        snippet = block_text[:snippet_max_len] + ("..." if len(block_text) > snippet_max_len else "")
                        if snippet not in description_snippets:
                             description_snippets.append(snippet)
                        break
                if len(description_snippets) >= 2:
                    break
        description = " | ".join(description_snippets)

        publication_date_str = self._find_date(content_area)
        if publication_date_str:
            print(f"Found date: {publication_date_str} in {page_url}")

        if title and (description or any(keyword in title.lower() for keyword in self.keywords)):
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

    def _find_date(self, content_area):
        if not content_area:
            return None
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
                try:
                    temp_date = date_candidate.lower()
                    gs_months = {'januar': '01', 'februar': '02', 'märz': '03', 'april': '04', 'mai': '05', 'juni': '06',
                                 'juli': '07', 'august': '08', 'september': '09', 'oktober': '10', 'november': '11', 'dezember': '12',
                                 'jan': '01', 'feb': '02', 'mrz': '03', 'apr': '04', 'jun': '06', 'jul': '07',
                                 'aug': '08', 'sep': '09', 'okt': '10', 'nov': '11', 'dez': '12'}
                    for m_de, m_num in gs_months.items():
                        temp_date = temp_date.replace(m_de, m_num)

                    formats_to_try = ["%d.%m.%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%y", "%d-%m-%y", "%d/%m/%y"]
                    parsed_date = None
                    for fmt in formats_to_try:
                        try:
                            # Remove delimiters for some formats
                            candidate_for_fmt = temp_date.replace('.','').replace('-','').replace('/','').replace(' ','')
                            parsed_date = datetime.strptime(candidate_for_fmt, fmt.replace('.','').replace('-','').replace('/','').replace(' ',''))
                            if parsed_date: break
                        except ValueError:
                            try:
                                parsed_date = datetime.strptime(date_candidate, fmt)
                                if parsed_date: break
                            except ValueError:
                                continue
                    if parsed_date:
                        return parsed_date.strftime('%Y-%m-%d')
                except Exception:
                    continue
        return None

    def _extract_text_with_ocr(self, pdf_path: str) -> str:
        try:
            images = convert_from_path(pdf_path)
            return "\n".join(pytesseract.image_to_string(img) for img in images)
        except Exception as e:
            print(f"OCR failed: {e}")
            return ""

    def download_pdf_to_text(self, pdf_url):
        print(f"Downloading PDF: {pdf_url}")
        temp_pdf_path = None
        try:
            response = self.session.get(pdf_url, timeout=45)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(response.content)
                temp_pdf_path = tmp_file.name

            text = ""
            try:
                with open(temp_pdf_path, 'rb') as f:
                    reader = PdfReader(f)
                    if reader.is_encrypted:
                        try:
                            reader.decrypt('')
                        except Exception:
                            print(f"Could not decrypt PDF {pdf_url}")
                            return None
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"PyPDF2 error while reading {pdf_url}: {e}.")

            if not text.strip():
                print(f"Warning: No text extracted from PDF, using OCR fallback: {pdf_url}")
                text = self._extract_text_with_ocr(temp_pdf_path)

            return text if text.strip() else None
        except requests.exceptions.RequestException as e:
            print(f"Error downloading PDF {pdf_url}: {e}")
            return None
        finally:
            if temp_pdf_path and os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

    def extract_data_from_pdf_text(self, pdf_url, pdf_text, source_municipality_name):
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
                    if any(keyword in title_candidate.lower() for keyword in self.keywords + ["bekanntmachung", "amtsblatt", "information", "satzung", "verordnung"]):
                        break
            if not title_candidate and lines:
                title_candidate = lines[0][:150] + "..." if len(lines[0]) > 150 else lines[0]

        description_snippets = []
        text_lower = pdf_text.lower()
        found_keywords_in_pdf_body = False
        for keyword in self.keywords:
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

        publication_date_str = self._find_date_in_pdf(pdf_text)
        if publication_date_str:
            print(f"Found date string in PDF '{publication_date_str}' for {pdf_url}")

        if found_keywords_in_pdf_body or any(keyword in title_candidate.lower() for keyword in self.keywords):
            extracted_items.append({
                'title': title_candidate if title_candidate else "PDF Content (Title not reliably extracted)",
                'description': description if description else "Keyword found in PDF.",
                'publication_date': publication_date_str if publication_date_str else "Not found",
                'url': pdf_url,
                'source': source_municipality_name,
                'type': 'PDF'
            })
        return extracted_items

    def _find_date_in_pdf(self, pdf_text):
        text_sample_for_date = pdf_text[:2000] + "\n" + pdf_text[-2000:]
        date_patterns = [
            r'(\b\d{1,2}\s*[\.\/-]\s*\d{1,2}\s*[\.\/-]\s*\d{2,4}\b)',
            r'(\b\d{4}\s*[\.\/-]\s*\d{1,2}\s*[\.\/-]\s*\d{1,2}\b)',
            r'(\d{1,2}\.\s*(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember|Jan\.|Feb\.|Mrz\.|Apr\.|Jun\.|Jul\.|Aug\.|Sep\.|Okt\.|Nov\.|Dez\.)\s*\d{2,4})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text_sample_for_date, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def scrape_site(self, site_name, site_url, max_html_links=15, max_pdf_links=10, delay=0.5):
        """Scrapes a single site and returns a list of extracted data items."""
        print(f"--- Processing {site_name} ({site_url}) ---")
        all_data = []
        processed_urls = set()

        main_page_html = self.fetch_html(site_url)
        if not main_page_html:
            return []

        html_links, pdf_links = self.find_relevant_links(main_page_html, site_url)
        print(f"Found {len(html_links)} relevant HTML links and {len(pdf_links)} PDF links.")

        for i, link_url in enumerate(html_links):
            if i >= max_html_links: break
            if link_url in processed_urls: continue
            time.sleep(delay)
            page_html = self.fetch_html(link_url)
            if page_html:
                data = self.extract_data_from_html_page(link_url, page_html, site_name)
                all_data.extend(data)
                processed_urls.add(link_url)

        for i, pdf_url in enumerate(pdf_links):
            if i >= max_pdf_links: break
            if pdf_url in processed_urls: continue
            time.sleep(delay)
            pdf_text = self.download_pdf_to_text(pdf_url)
            if pdf_text:
                data = self.extract_data_from_pdf_text(pdf_url, pdf_text, site_name)
                all_data.extend(data)
                processed_urls.add(pdf_url)

        return all_data

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
            all_keys = set(key for row in data for key in row.keys())
            headers = sorted(list(all_keys))
            with open(csv_filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
            print(f"Successfully saved {len(data)} items to {csv_filepath}")
    except IOError as e:
        print(f"Error saving data to CSV file {csv_filepath}: {e}")


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

    scraper = Scraper()
    all_extracted_data = []
    output_dir = "output_data"
    os.makedirs(output_dir, exist_ok=True)
    json_output_file = os.path.join(output_dir, "extracted_data.json")
    csv_output_file = os.path.join(output_dir, "extracted_data.csv")

    for site_name, site_url in TARGET_SITES.items():
        results = scraper.scrape_site(site_name, site_url)
        all_extracted_data.extend(results)
        print(f"--- Finished {site_name}. Collected {len(results)} items. Total: {len(all_extracted_data)} ---")

    print(f"\n--- Total {len(all_extracted_data)} items extracted ---")
    if all_extracted_data:
        save_data(all_extracted_data, json_filepath=json_output_file, csv_filepath=csv_output_file)
    else:
        print("No data extracted.")
    print(f"\nScript finished. Check '{json_output_file}' and '{csv_output_file}'.")
