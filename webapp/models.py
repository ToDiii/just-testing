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
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow)
    last_scraped_at = Column(DateTime, nullable=True)

    results = relationship("ScrapeResult", back_populates="target")


class ScrapeResult(Base):
    __tablename__ = "scrape_results"

    id = Column(Integer, primary_key=True, index=True)
    target_id = Column(Integer, ForeignKey("target_sites.id"))
    title = Column(String)
    description = Column(Text)
    publication_date = Column(String)
    url = Column(String)
    source = Column(String)
    type = Column(String)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    target = relationship("TargetSite", back_populates="results")


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, unique=True, index=True, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)


class GlobalState(Base):
    __tablename__ = "global_state"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    last_scrape_start = Column(DateTime, nullable=True)
    last_scrape_end = Column(DateTime, nullable=True)
    scrape_status = Column(String, default="idle")
