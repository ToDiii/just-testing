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
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    added_at: datetime
    last_scraped_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class GlobalStateBase(BaseModel):
    last_scrape_start: Optional[datetime] = None
    last_scrape_end: Optional[datetime] = None
    scrape_status: str


class GlobalState(GlobalStateBase):
    id: int
    key: str

    class Config:
        orm_mode = True


class ScrapeResultBase(BaseModel):
    title: str
    description: str
    publication_date: str
    url: str
    source: str
    type: str
    category_id: Optional[int] = None


class ScrapeResultCreate(ScrapeResultBase):
    target_id: int


class ScrapeResult(ScrapeResultBase):
    id: int
    scraped_at: datetime

    class Config:
        orm_mode = True


class TargetWithResults(TargetSite):
    results: List[ScrapeResult] = []


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int

    class Config:
        orm_mode = True


class KeywordBase(BaseModel):
    word: str
    category_id: Optional[int] = None


class KeywordCreate(KeywordBase):
    pass


class Keyword(KeywordBase):
    id: int
    added_at: datetime
    category: Optional[Category] = None

    class Config:
        orm_mode = True
