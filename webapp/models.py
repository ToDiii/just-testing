from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


from sqlalchemy import Float

class TargetSite(Base):
    __tablename__ = "target_sites"

    id = Column(Integer, primary_key=True, index=True)
    gemeindeschluessel = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=True)
    postleitzahl = Column(String, index=True, nullable=True)
    url = Column(String, unique=True, nullable=False)
    region_id = Column(Integer, ForeignKey("regions.id"), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    last_scraped_at = Column(DateTime, nullable=True)

    results = relationship("ScrapeResult", back_populates="target")
    region = relationship("Region", back_populates="targets")


class ScrapeResult(Base):
    __tablename__ = "scrape_results"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("target_sites.id"))
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    title = Column(String)
    description = Column(Text)
    publication_date = Column(String)
    url = Column(String)
    source = Column(String)
    type = Column(String)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    is_ignored = Column(Integer, default=0) # 0 = active, 1 = ignored (deleted)

    target = relationship("TargetSite", back_populates="results")
    category = relationship("Category")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    keywords = relationship("Keyword", back_populates="category")


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, unique=True, index=True, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="keywords")


class GlobalState(Base):
    __tablename__ = "global_state"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    last_scrape_start = Column(DateTime, nullable=True)
    last_scrape_end = Column(DateTime, nullable=True)
    scrape_status = Column(String, default="idle")


class NotificationConfig(Base):
    __tablename__ = "notification_configs"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # "email" or "webhook"
    recipient = Column(String, nullable=False)  # email address or webhook URL
    enabled = Column(Integer, default=1)  # 1 for true, 0 for false (using Integer for SQLite boolean)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScrapingConfig(Base):
    __tablename__ = "scraping_configs"

    id = Column(Integer, primary_key=True, index=True)
    max_html_links = Column(Integer, default=15)
    max_pdf_links = Column(Integer, default=10)
    request_delay = Column(Float, default=0.5)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    type = Column(String, nullable=False)  # "country", "state", "region"
    parent_id = Column(Integer, ForeignKey("regions.id"), nullable=True)

    parent = relationship("Region", remote_side=[id], backref="children")
    targets = relationship("TargetSite", back_populates="region")
