import os
import sys

# Add project root to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from webapp.database import SessionLocal
from webapp.models import Region

def seed_regions():
    db = SessionLocal()
    try:
        # Check if regions already exist
        if db.query(Region).first():
            print("Regions already seeded.")
            return

        # 1. Country
        germany = Region(name="Deutschland", type="country")
        db.add(germany)
        db.flush()

        # 2. States (Bundesländer) - Just a few examples
        bavaria = Region(name="Bayern", type="state", parent_id=germany.id)
        berlin = Region(name="Berlin", type="state", parent_id=germany.id)
        saxony = Region(name="Sachsen", type="state", parent_id=germany.id)
        db.add_all([bavaria, berlin, saxony])
        db.flush()

        # 3. Regions/Districts (Regierungsbezirke/Landkreise)
        oberbayern = Region(name="Oberbayern", type="region", parent_id=bavaria.id)
        niederbayern = Region(name="Niederbayern", type="region", parent_id=bavaria.id)
        db.add_all([oberbayern, niederbayern])
        
        db.commit()
        print("Regions seeded successfully.")
    except Exception as e:
        print(f"Error seeding regions: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_regions()
