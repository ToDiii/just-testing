import sys
import os
from sqlalchemy.orm import Session

# Add project root to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from webapp.database import SessionLocal, engine
from webapp.models import TargetSite, Base

# Researched data for the user's specified postal codes
SEED_DATA = [
    {
        "plz": "84416",
        "name": "Taufkirchen (Vils)",
        "url": "https://www.taufkirchen.de/",
        "lat": 48.349, "lon": 12.13,
        "gkz": "09177139"
    },
    {
        "plz": "84439",
        "name": "Steinkirchen",
        "url": "https://www.gemeinde-steinkirchen.de/",
        "lat": 48.374, "lon": 12.078,
        "gkz": "09177138"
    },
    {
        "plz": "84432",
        "name": "Hohenpolding",
        "url": "https://www.hohenpolding.de/",
        "lat": 48.384, "lon": 12.131,
        "gkz": "09177121"
    },
    {
        "plz": "84424",
        "name": "Isen",
        "url": "https://www.markt-isen.de/",
        "lat": 48.216, "lon": 12.066,
        "gkz": "09177123"
    },
    {
        "plz": "84434",
        "name": "Kirchberg",
        "url": "https://www.gemeinde-kirchberg.de/",
        "lat": 48.405, "lon": 12.048,
        "gkz": "09177124"
    },
    {
        "plz": "84428",
        "name": "Buchbach",
        "url": "https://www.buchbach.de/",
        "lat": 48.316, "lon": 12.283,
        "gkz": "09183114"
    }
]

def seed_database():
    """
    Ensures that a specific set of test municipalities exist in the database
    with their correct, real URLs and postal codes.
    """
    db: Session = SessionLocal()
    print("Seeding database with specified test municipalities...")

    for item in SEED_DATA:
        target = db.query(TargetSite).filter(TargetSite.gemeindeschluessel == item["gkz"]).first()

        if target:
            print(f"Found existing entry for {item['name']}. Updating with correct seed data.")
            target.url = item["url"]
            target.postleitzahl = item["plz"]
            target.name = item["name"]
            target.latitude = item["lat"]
            target.longitude = item["lon"]
        else:
            print(f"Creating new entry for {item['name']}.")
            new_target = TargetSite(
                gemeindeschluessel=item["gkz"],
                name=item["name"],
                postleitzahl=item["plz"],
                url=item["url"],
                latitude=item["lat"],
                longitude=item["lon"]
            )
            db.add(new_target)

    try:
        db.commit()
        print("Database seeding complete. All specified municipalities are present and correct.")
    except Exception as e:
        print(f"An error occurred during database commit: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("Starting the database seed process for test data.")

    Base.metadata.create_all(bind=engine)

    seed_database()

    print("Seed process finished.")