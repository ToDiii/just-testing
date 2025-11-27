
import sys
import os
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from webapp.models import TargetSite, Keyword

# Add the current directory to the path
sys.path.append(os.getcwd())

# Setup DB connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./webapp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

from scraper_lib.parser import find_relevant_links

# ... (imports)

def analyze_links(target_id=None, url=None):
    db = SessionLocal()
    try:
        # Get keywords
        keywords = [k.word for k in db.query(Keyword).all()]
        if not keywords:
            keywords = ["Baugebiet", "Bebauungsplan", "Grundstück", "Ausschreibung"]
        
        print(f"Keywords: {keywords}")
        
        target_url = url
        target_name = "Custom URL"
        
        if not target_url:
            # Get target from DB
            if target_id:
                target = db.get(TargetSite, target_id)
            else:
                target = db.query(TargetSite).first()
                
            if not target:
                print("No target found.")
                return
            target_url = target.url
            target_name = target.name

        print(f"Analyzing Target: {target_name} ({target_url})")
        
        response = requests.get(target_url)
        html_content = response.text
        
        html_links, pdf_links = find_relevant_links(html_content, target_url, keywords)
        
        print(f"\nTotal HTML Links Found by Parser: {len(html_links)}")
        print(f"Total PDF Links Found by Parser: {len(pdf_links)}")
        
        print("\n--- HTML Links ---")
        for l in html_links:
            print(f"[x] {l}")
            
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith("http"):
            analyze_links(url=arg)
        else:
            analyze_links(target_id=int(arg))
    else:
        analyze_links()
