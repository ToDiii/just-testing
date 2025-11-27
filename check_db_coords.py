
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from webapp.models import TargetSite, Base

# Add the current directory to the path
sys.path.append(os.getcwd())

# Setup DB connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./webapp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_db():
    db = SessionLocal()
    try:
        targets = db.query(TargetSite).all()
        print(f"Total targets: {len(targets)}")
        
        valid_coords = 0
        for t in targets:
            print(f"ID: {t.id}, Name: {t.name}, Lat: {t.latitude}, Lon: {t.longitude}")
            if t.latitude is not None and t.longitude is not None:
                valid_coords += 1
        
        print(f"Targets with valid coords: {valid_coords}")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_db()
