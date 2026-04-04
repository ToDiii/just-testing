from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class TargetSiteBase(BaseModel):
    url: str
    name: Optional[str] = None
    region_id: Optional[int] = None
    source_type: str = "website"  # "website" | "rss"


class TargetSiteCreate(TargetSiteBase):
    pass


class RegionBase(BaseModel):
    name: str
    type: str  # "country", "state", "region"
    parent_id: Optional[int] = None


class RegionCreate(RegionBase):
    pass


class Region(RegionBase):
    id: int

    class Config:
        from_attributes = True


class TargetSite(TargetSiteBase):
    id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    added_at: datetime
    last_scraped_at: Optional[datetime] = None
    region: Optional[Region] = None

    class Config:
        from_attributes = True


class GlobalStateBase(BaseModel):
    last_scrape_start: Optional[datetime] = None
    last_scrape_end: Optional[datetime] = None
    scrape_status: str


class GlobalState(GlobalStateBase):
    id: int
    key: str

    class Config:
        from_attributes = True


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
    is_ignored: int = 0

    class Config:
        from_attributes = True


class TargetWithResults(TargetSite):
    results: List[ScrapeResult] = []


class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int

    class Config:
        from_attributes = True


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
        from_attributes = True


class NotificationConfigBase(BaseModel):
    type: str
    recipient: str
    enabled: bool = True


class NotificationConfigCreate(NotificationConfigBase):
    pass


class NotificationConfig(NotificationConfigBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScrapingConfigBase(BaseModel):
    max_html_links: int = 15
    max_pdf_links: int = 10
    request_delay: float = 0.5
    scraper_engine: str = "requests"  # "requests" | "crawl4ai"
    crawl4ai_server_url: Optional[str] = None  # e.g. "http://192.168.1.100:11235"
    crawl4ai_fallback: bool = True             # fall back to requests on crawl4ai failure
    max_targets_per_run: int = 500            # 0 = unlimited


class ScrapingConfigCreate(ScrapingConfigBase):
    pass


class ScrapingConfig(ScrapingConfigBase):
    id: int
    updated_at: datetime

    class Config:
        orm_mode = True


DEFAULT_SYSTEM_PROMPT = """Du bist ein Experte für kommunale Bauleitplanung und Grundstücksentwicklung in Deutschland.
Analysiere die folgenden Scraping-Ergebnisse und fasse die wichtigsten Informationen zusammen.
Fokussiere dich auf: Baugebiete, Bebauungspläne, Flächennutzungspläne, Grundstücksverkäufe, Ausschreibungen.
Gib eine strukturierte Zusammenfassung auf Deutsch aus. Hebe besonders interessante oder dringende Themen hervor."""


class AIConfigBase(BaseModel):
    provider: str = "openrouter"
    api_key: str
    base_url: Optional[str] = None
    model_name: str = "openai/gpt-4o-mini"
    system_prompt: Optional[str] = None
    enabled: bool = True


class AIConfigCreate(AIConfigBase):
    pass


class AIConfigResponse(AIConfigBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class AIAnalysisResponse(BaseModel):
    id: int
    created_at: datetime
    result_text: Optional[str] = None
    result_count: Optional[int] = None
    mode: str

    class Config:
        from_attributes = True


class AIAnalyzeRequest(BaseModel):
    result_ids: List[int]
    mode: str = "summary"
