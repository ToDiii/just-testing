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

        # Create regions table
        print("Creating regions table...")
        from webapp.models import Region
        Region.__table__.create(engine, checkfirst=True)

        # Add region_id column to target_sites table
        print("Adding region_id column to target_sites table...")
        try:
            connection.execute(text("ALTER TABLE target_sites ADD COLUMN region_id INTEGER REFERENCES regions(id)"))
            print("Column added successfully.")
        except Exception as e:
            print(f"Column might already exist or error occurred: {e}")

        # Create notification_configs table
        print("Creating notification_configs table...")
        from webapp.models import NotificationConfig
        NotificationConfig.__table__.create(engine, checkfirst=True)

        # Create scraping_configs table
        print("Creating scraping_configs table...")
        from webapp.models import ScrapingConfig
        ScrapingConfig.__table__.create(engine, checkfirst=True)

        # Insert default config if not exists
        with engine.begin() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM scraping_configs"))
            if result.scalar() == 0:
                conn.execute(text("INSERT INTO scraping_configs (max_html_links, max_pdf_links, request_delay) VALUES (15, 10, 0.5)"))
                print("Inserted default scraping configuration.")

if __name__ == "__main__":
    migrate_db()
