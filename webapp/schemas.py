from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class TargetSiteBase(BaseModel):
    url: str
    name: Optional[str] = None


class TargetSiteCreate(TargetSiteBase):
    pass


class TargetSite(TargetSiteBase):
    id: int
    added_at: datetime

    class Config:
        orm_mode = True


class ScrapeResultBase(BaseModel):
    title: str
    description: str
    publication_date: str
    url: str
    source: str
    type: str


class ScrapeResultCreate(ScrapeResultBase):
    target_id: int


class ScrapeResult(ScrapeResultBase):
    id: int
    scraped_at: datetime

    class Config:
        orm_mode = True


class TargetWithResults(TargetSite):
    results: List[ScrapeResult] = []
