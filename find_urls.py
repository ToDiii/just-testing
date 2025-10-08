import sys
import os
import time
import argparse
from sqlalchemy.orm import Session
from sqlalchemy import or_

# Add project root to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from webapp.database import SessionLocal, engine
from webapp.models import TargetSite, Base
from unidecode import unidecode
import re
from urllib.parse import urlparse

# The google_search tool is available in the execution environment.

def sanitize_name_for_url(name: str) -> str:
    """Sanitizes a municipality name for URL comparison."""
    name = unidecode(name.lower())
    name = re.sub(r'^(stadt|gemeinde|markt|landkreis)\s+', '', name)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def find_best_url(search_results: list[dict], municipality_name: str) -> str | None:
    """Applies heuristics to find the best URL from a list of search results."""
    if not search_results:
        return None

    sanitized_name = sanitize_name_for_url(municipality_name)
    candidates = []
    for result in search_results[:5]: # Check top 5 results
        url = result.get('url')
        if not url:
            continue

        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        path = parsed_url.path.lower()

        if any(banned in domain for banned in ['facebook', 'twitter', 'youtube', 'wikipedia', 'wiktionary', 'instagram']):
            continue
        if not domain.endswith(('.de', '.com')):
             continue

        score = 0
        if not domain.endswith('.de'):
            score -= 10
        if any(keyword in url.lower() for keyword in ['rathaus', 'stadt', 'gemeinde', 'landkreis', 'vg-', 'markt-']):
            score += 5
        if sanitized_name in domain:
            score += 20
        elif sanitized_name in path:
            score += 10

        candidates.append({'url': url, 'score': score})

    if not candidates:
        return None

    best_candidate = sorted(candidates, key=lambda x: x['score'], reverse=True)[0]
    if best_candidate['score'] > 0:
        return best_candidate['url']
    return None

def get_targets_to_update(db: Session, limit: int = None):
    """
    Fetches targets with placeholder URLs, optionally limiting the count.
    """
    query = db.query(TargetSite).filter(
        or_(
            TargetSite.url.like('http://placeholder.url/%'),
            TargetSite.url.is_(None)
        )
    )
    if limit:
        query = query.limit(limit)
    return query.all()

def find_and_update_urls(limit: int = None):
    """
    Main logic to find and update URLs for municipalities.
    """
    db: Session = SessionLocal()
    targets_to_update = get_targets_to_update(db, limit)

    print(f"Found {len(targets_to_update)} municipalities with placeholder URLs to process.")
    if not targets_to_update:
        db.close()
        return

    for i, target in enumerate(targets_to_update):
        print(f"\n--- Processing {i+1}/{len(targets_to_update)}: {target.name} ---")
        query = f"offizielle webseite gemeinde {target.name}"
        print(f"Searching for: '{query}'")

        try:
            search_results = google_search(query)
            best_url = find_best_url(search_results, target.name)

            if best_url:
                print(f"Found best URL: {best_url}. Updating database...")
                target.url = best_url
                db.commit()
                print("Update successful.")
            else:
                print("Could not determine a confident URL from search results.")

        except Exception as e:
            print(f"An error occurred during search: {e}")
            db.rollback()

        # Add a delay to be respectful to the search API
        if i < len(targets_to_update) - 1:
            print("Waiting for 2 seconds before next search...")
            time.sleep(2)

    print("\nURL finding process finished.")
    db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find official URLs for municipalities using Google Search.")
    parser.add_argument('--limit', type=int, help="Limit the number of municipalities to process.")

    args = parser.parse_args()

    print("Starting the process to find official URLs for municipalities.")

    Base.metadata.create_all(bind=engine)

    find_and_update_urls(limit=args.limit)

    print("Process complete.")