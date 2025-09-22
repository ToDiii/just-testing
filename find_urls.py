import sys
import os
import time
from sqlalchemy.orm import Session
from sqlalchemy import or_

# Add project root to the Python path to allow importing from 'webapp'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from webapp.database import SessionLocal
from webapp.models import TargetSite
from unidecode import unidecode
import re
from urllib.parse import urlparse

# The google_search tool is available in the execution environment.
# We will call it directly in the code.

def sanitize_name_for_url(name: str) -> str:
    """Sanitizes a municipality name for URL comparison."""
    # Lowercase, remove umlauts, and remove generic terms
    name = unidecode(name.lower())
    name = re.sub(r'^(stadt|gemeinde|markt|landkreis)\s+', '', name)
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

def find_best_url(search_results: list[dict], municipality_name: str) -> str | None:
    """
    Applies heuristics to find the best URL from a list of search results.
    """
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

        # Basic filtering
        if any(banned in domain for banned in ['facebook', 'twitter', 'youtube', 'wikipedia', 'wiktionary', 'instagram']):
            continue
        if not domain.endswith('.de') and not domain.endswith('.com'): # Allow .com but prefer .de
             continue

        score = 0
        # Heavily penalize non .de domains
        if not domain.endswith('.de'):
            score -= 10

        # Promote official-sounding keywords
        if any(keyword in url.lower() for keyword in ['rathaus', 'stadt', 'gemeinde', 'landkreis', 'vg-', 'markt-']):
            score += 5

        # Promote if sanitized name is in the domain
        if sanitized_name in domain:
            score += 20
        # Lesser promotion if in path
        elif sanitized_name in path:
            score += 10

        candidates.append({'url': url, 'score': score})

    if not candidates:
        return None

    # Sort by score descending and return the best URL
    best_candidate = sorted(candidates, key=lambda x: x['score'], reverse=True)[0]

    # Only return if the score is positive, otherwise we are not confident
    if best_candidate['score'] > 0:
        return best_candidate['url']

    return None


def get_targets_without_real_url(db: Session):
    """
    Fetches all targets from the database that have a placeholder URL.
    """
    return db.query(TargetSite).filter(
        or_(
            TargetSite.url.like('http://placeholder.url/%'),
            TargetSite.url.is_(None)
        )
    ).all()

def find_and_update_urls():
    """
    Main logic to find and update URLs for municipalities.
    """
    db: Session = SessionLocal()

    # DEBUG: Count all targets to verify DB connection
    total_count = db.query(TargetSite).count()
    print(f"DEBUG: Total targets found in database: {total_count}")

    targets_to_update = get_targets_without_real_url(db)
    print(f"Found {len(targets_to_update)} municipalities with placeholder URLs to process.")

    for i, target in enumerate(targets_to_update):
        print(f"\\n--- Processing {i+1}/{len(targets_to_update)}: {target.name} ---")

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

        # Add a delay to be respectful to the search API
        print("Waiting for 2 seconds before next search...")
        time.sleep(2)

    print("\\nURL finding process finished.")
    db.close()


if __name__ == "__main__":
    print("Starting the process to find official URLs for municipalities.")

    # Ensure the tables are created before starting
    from webapp.database import engine
    from webapp.models import Base
    print("Ensuring database schema exists...")
    Base.metadata.create_all(bind=engine)

    find_and_update_urls()
    print("Process complete.")
