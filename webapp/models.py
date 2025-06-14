from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from .database import Base


class TargetSite(Base):
    __tablename__ = "target_sites"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    url = Column(String, unique=True, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)

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
