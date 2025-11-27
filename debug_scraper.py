
import sys
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from webapp.models import TargetSite, Keyword

# Add the current directory to the path
sys.path.append(os.getcwd())

from scraper import Scraper

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Setup DB connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./webapp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_scrape(target_id=None):
    db = SessionLocal()
    try:
        # Get keywords
        keywords_db = db.query(Keyword).all()
        if not keywords_db:
            print("No keywords found in DB. Using defaults.")
            keywords = [
                {"word": "Baugebiet", "category_id": None},
                {"word": "Bebauungsplan", "category_id": None}
            ]
        else:
            keywords = [{"word": k.word, "category_id": k.category_id} for k in keywords_db]
        
        print(f"Keywords: {[k['word'] for k in keywords]}")
        
        # Get target
        if target_id:
            target = db.get(TargetSite, target_id)
        else:
            target = db.query(TargetSite).first()
            
        if not target:
            print("No target found.")
            return

        print(f"Scraping Target: {target.name} ({target.url})")
        
        scraper = Scraper(keywords=keywords)
        results = scraper.scrape_site(target.name, target.url)
        
        print(f"\nFound {len(results)} results:")
        for r in results:
            print(f"- [{r['type']}] {r['title']} ({r['publication_date']})")
            print(f"  Category ID: {r.get('category_id')}")
            print(f"  URL: {r['url']}")
            print(f"  Desc: {r['description'][:100]}...")
            
    finally:
        db.close()

if __name__ == "__main__":
    # You can pass a target_id as an argument
    tid = int(sys.argv[1]) if len(sys.argv) > 1 else None
    debug_scrape(tid)
