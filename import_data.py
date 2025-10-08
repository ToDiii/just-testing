import requests
import json
import sys
import os
import argparse
from sqlalchemy.orm import Session

# Add project root to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from webapp.database import SessionLocal, engine
from webapp.models import TargetSite, Base

# API endpoints for the two datasets
GEMEINDE_API_URL = "https://data.opendatasoft.com/api/v2/catalog/datasets/georef-germany-gemeinde@public/exports/json"
PLZ_API_URL = "https://data.opendatasoft.com/api/v2/catalog/datasets/georef-germany-postleitzahl@public/exports/json"

def fetch_data(url, limit=None):
    """Fetches data from an Opendatasoft API endpoint."""
    params = {"rows": limit if limit else -1, "pretty": "false", "timezone": "UTC"}
    print(f"Downloading data from {url}...")
    try:
        response = requests.get(url, params=params, headers={'User-Agent': 'MunicipalityScraper/1.0'})
        response.raise_for_status()
        data = response.json()
        print(f"Successfully downloaded {len(data)} records.")
        return data
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error downloading or parsing data from {url}: {e}")
        return None

def create_plz_map(plz_data):
    """Creates a mapping from municipality name to postal code."""
    plz_map = {}
    if not plz_data:
        return plz_map

    # The relevant keys are 'plz_name' for the municipality name
    # and 'plz_code' for the postal code.
    for record in plz_data:
        name = record.get('plz_name')
        plz = record.get('plz_code')
        if name and plz:
            # A city can have multiple postal codes. We store them all.
            if name not in plz_map:
                plz_map[name] = []
            plz_map[name].append(plz)
    return plz_map

def import_full_data(limit=None):
    """
    Downloads and combines municipality and postal code data, then imports it.
    """
    # Step 1: Fetch PLZ data and create a mapping
    plz_data = fetch_data(PLZ_API_URL, limit=limit) # Also limit PLZ data for testing
    plz_map = create_plz_map(plz_data)

    if not plz_map:
        print("Could not create PLZ map. Aborting.")
        return

    # Step 2: Fetch Gemeinde data
    gemeinde_data = fetch_data(GEMEINDE_API_URL, limit=limit)
    if not gemeinde_data:
        print("Could not fetch Gemeinde data. Aborting.")
        return

    # Step 3: Connect to DB and process
    db: Session = SessionLocal()
    existing_keys = {key[0] for key in db.query(TargetSite.gemeindeschluessel).filter(TargetSite.gemeindeschluessel.isnot(None)).all()}
    print(f"Found {len(existing_keys)} existing keys in the database.")

    new_targets = []
    skipped_count = 0

    print("Processing and combining records...")
    for record in gemeinde_data:
        gem_code_list = record.get('gem_code')
        gkz = gem_code_list[0] if gem_code_list else None

        if not gkz or gkz in existing_keys:
            skipped_count += 1
            continue

        name_list = record.get('gem_name')
        name = name_list[0] if name_list else 'N/A'

        # Look up the postal code from our map. Use the first one if multiple exist.
        plz_list = plz_map.get(name)
        plz = plz_list[0] if plz_list else None

        center = record.get('geo_point_2d', {})
        lat = center.get('lat')
        lon = center.get('lon')

        placeholder_url = f"http://placeholder.url/gkz/{gkz}"

        new_target = TargetSite(
            gemeindeschluessel=gkz,
            name=name,
            postleitzahl=plz,
            url=placeholder_url,
            latitude=lat,
            longitude=lon
        )
        new_targets.append(new_target)
        existing_keys.add(gkz)

    print(f"Skipped {skipped_count} records.")

    if not new_targets:
        print("No new municipalities to import.")
        db.close()
        return

    print(f"Adding {len(new_targets)} new municipalities to the database session...")
    try:
        db.add_all(new_targets)
        db.commit()
        print("Import successful.")
    except Exception as e:
        print(f"An error occurred during database commit: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import municipality and postal code data.")
    parser.add_argument('--limit', type=int, help="Limit the number of records to process for testing.")
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    import_full_data(limit=args.limit)
    print("Import process finished.")