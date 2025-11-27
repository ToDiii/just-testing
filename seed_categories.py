
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from webapp.models import Category, Keyword

# Add the current directory to the path
sys.path.append(os.getcwd())

# Setup DB connection
SQLALCHEMY_DATABASE_URL = "sqlite:///./webapp.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def seed_categories():
    db = SessionLocal()
    try:
        print("Seeding categories...")
        
        # Define categories
        categories_data = {
            "Baugebiet": ["baugebiet", "neubaugebiet", "bauland", "bauplatz", "grundstück", "verkauf", "entwicklung"],
            "Planung": ["bebauungsplan", "flächennutzungsplan", "satzung", "verordnung", "sanierung"],
            "Ausschreibung": ["ausschreibung", "stellenausschreibung", "vergabe"],
            "Sonstiges": []
        }
        
        category_map = {}
        
        # Create Categories
        for cat_name in categories_data:
            category = db.query(Category).filter_by(name=cat_name).first()
            if not category:
                print(f"Creating category: {cat_name}")
                category = Category(name=cat_name)
                db.add(category)
                db.commit()
                db.refresh(category)
            else:
                print(f"Category exists: {cat_name}")
            category_map[cat_name] = category.id
            
        # Assign Keywords
        print("\nAssigning keywords...")
        keywords = db.query(Keyword).all()
        for k in keywords:
            word = k.word.lower()
            assigned = False
            for cat_name, cat_keywords in categories_data.items():
                if any(ck in word for ck in cat_keywords):
                    k.category_id = category_map[cat_name]
                    print(f"  '{k.word}' -> {cat_name}")
                    assigned = True
                    break
            
            if not assigned:
                k.category_id = category_map["Sonstiges"]
                print(f"  '{k.word}' -> Sonstiges")
                
        db.commit()
        print("\nSeeding complete.")
            
    finally:
        db.close()

if __name__ == "__main__":
    seed_categories()
