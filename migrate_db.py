import sys
import os
from sqlalchemy import text

# Add project root to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from webapp.database import engine, Base
from webapp.models import Category

def migrate_db():
    print("Migrating database schema...")
    with engine.connect() as connection:
        # Create categories table
        print("Creating categories table...")
        # We use SQLAlchemy's metadata to create the table if it doesn't exist
        Category.__table__.create(engine, checkfirst=True)
        
        # Add category_id column to keywords table
        print("Adding category_id column to keywords table...")
        try:
            connection.execute(text("ALTER TABLE keywords ADD COLUMN category_id INTEGER REFERENCES categories(id)"))
            print("Column added successfully.")
        except Exception as e:
            print(f"Column might already exist or error occurred: {e}")

        # Add category_id column to scrape_results table
        print("Adding category_id column to scrape_results table...")
        try:
            connection.execute(text("ALTER TABLE scrape_results ADD COLUMN category_id INTEGER REFERENCES categories(id)"))
            print("Column added successfully.")
        except Exception as e:
            print(f"Column might already exist or error occurred: {e}")

if __name__ == "__main__":
    migrate_db()
