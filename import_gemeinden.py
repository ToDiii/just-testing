import requests
import json
import sys
import os
from sqlalchemy.orm import Session

# Add project root to the Python path to allow importing from 'webapp'
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from webapp.database import SessionLocal, engine
from webapp.models import TargetSite, Base

# The API endpoint for the JSON data source from OpenDataSoft
API_BASE_URL = "https://data.opendatasoft.com/api/v2/catalog/datasets/georef-germany-gemeinde@public/exports/json"

def import_data():
    """
    Downloads municipality data and imports it into the database.
    """
    print("Downloading municipality data from API...")

    params = {
        "rows": -1,  # -1 means all records
        "pretty": "false",
        "timezone": "UTC"
    }

    try:
        response = requests.get(API_BASE_URL, params=params, headers={'User-Agent': 'MunicipalityScraper/1.0'})
        response.raise_for_status()
        data = response.json()
        print(f"Successfully downloaded {len(data)} records.")
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error downloading or parsing data: {e}")
        return

    db: Session = SessionLocal()

    print("Querying existing municipality keys from the database...")
    existing_keys = {key[0] for key in db.query(TargetSite.gemeindeschluessel).filter(TargetSite.gemeindeschluessel.isnot(None)).all()}
    print(f"Found {len(existing_keys)} existing keys.")

    new_targets = []
    skipped_count = 0

    print("Processing records and preparing new entries...")
    for record in data:
        # Data is a direct list of records, no 'fields' key.
        gem_code_list = record.get('gem_code')
        gem_code = gem_code_list[0] if gem_code_list else None

        if not gem_code or gem_code in existing_keys:
            skipped_count += 1
            continue

        # Extract coordinates from the 'geo_point_2d' dictionary
        geo_point = record.get('geo_point_2d', {})
        lat = geo_point.get('lat')
        lon = geo_point.get('lon')

        # Extract name
        gem_name_list = record.get('gem_name')
        gem_name = gem_name_list[0] if gem_name_list else 'N/A'

        # Create a placeholder URL
        placeholder_url = f"http://placeholder.url/gemeinde/{gem_code}"

        new_target = TargetSite(
            gemeindeschluessel=gem_code,
            name=gem_name,
            url=placeholder_url,
            latitude=lat,
            longitude=lon
        )
        new_targets.append(new_target)
        existing_keys.add(gem_code) # Add to set to handle duplicates within the JSON file itself

    print(f"Skipped {skipped_count} records (already exist or no key).")

    if not new_targets:
        print("No new municipalities to import.")
        db.close()
        return

    print(f"Adding {len(new_targets)} new municipalities to the database session...")

    # Add to session and commit
    try:
        db.add_all(new_targets)
        db.commit()
        print(f"Successfully imported {len(new_targets)} new municipalities.")
    except Exception as e:
        print(f"An error occurred during database commit: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting the municipality import process.")

    # Ensure the tables are created
    Base.metadata.create_all(bind=engine)

    import_data()

    print("Import process finished.")
