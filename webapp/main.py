from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from . import models, schemas
from .database import SessionLocal, engine
from scraper import Scraper, PREDEFINED_TARGETS
from .routes import router as api_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Scraper Web API")

# API router
app.include_router(api_router, prefix="/api")

# Instantiate the scraper once
scraper_instance = Scraper()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# The API endpoints are now defined in the router, so they are removed from here.
# We keep the helper functions and startup events.

def scrape_single_target(target: models.TargetSite, db: Session, scraper_instance: Scraper) -> int:
    """Scrape a single target site using the Scraper class and return the number of new results."""
    site_name = target.name or target.url
    results = scraper_instance.scrape_site(site_name, target.url)

    new_count = 0
    for item in results:
        exists = db.query(models.ScrapeResult).filter_by(url=item['url'], target_id=target.id).first()
        if not exists:
            db_item = models.ScrapeResult(target_id=target.id, **item)
            db.add(db_item)
            new_count += 1

    db.commit()
    return new_count


def init_targets(db: Session) -> None:
    """Initialize database with predefined targets if they don't exist."""
    existing_urls = {t.url for t in db.query(models.TargetSite.url).all()}
    new_targets = []
    for url in PREDEFINED_TARGETS:
        if url not in existing_urls:
            new_targets.append(models.TargetSite(url=url, name=url.split('.')[1]))
    if new_targets:
        db.add_all(new_targets)
        db.commit()
        print(f"Added {len(new_targets)} new predefined targets.")


@app.on_event("startup")
def startup_populate():
    db = SessionLocal()
    try:
        init_targets(db)
    finally:
        db.close()

# Serve Svelte app
if os.path.exists("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    return FileResponse('dist/index.html')


@app.post("/targets/", response_model=schemas.TargetSite)
def create_target(target: schemas.TargetSiteCreate, db: Session = Depends(get_db)):
    db_target = db.query(models.TargetSite).filter(models.TargetSite.url == target.url).first()
    if db_target:
        raise HTTPException(status_code=400, detail="Target already exists")
    db_target = models.TargetSite(url=target.url, name=target.name)
    db.add(db_target)
    db.commit()
    db.refresh(db_target)
    return db_target


@app.get("/targets/", response_model=List[schemas.TargetSite])
def read_targets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.TargetSite).offset(skip).limit(limit).all()


def scrape_single_target(target: models.TargetSite, db: Session) -> int:
    """Scrape a single target site using the Scraper class and return the number of new results."""
    site_name = target.name or target.url
    results = scraper_instance.scrape_site(site_name, target.url)

    new_count = 0
    for item in results:
        # Check if a result with the same URL already exists for this target
        exists = db.query(models.ScrapeResult).filter_by(url=item['url'], target_id=target.id).first()
        if not exists:
            db_item = models.ScrapeResult(target_id=target.id, **item)
            db.add(db_item)
            new_count += 1

    db.commit()
    return new_count


@app.post("/scrape")
def scrape_targets(db: Session = Depends(get_db)):
    targets = db.query(models.TargetSite).all()
    if not targets:
        raise HTTPException(status_code=400, detail="No targets configured")
    summary = []
    for target in targets:
        count = scrape_single_target(target, db)
        summary.append({"target_id": target.id, "name": target.name, "new_results": count})
    return {"status": "scrape_complete", "summary": summary}


@app.post("/scrape/{target_id}")
def scrape_target(target_id: int, db: Session = Depends(get_db)):
    target = db.get(models.TargetSite, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    new_count = scrape_single_target(target, db)
    timestamp = datetime.utcnow()
    return {"target_id": target_id, "new_results": new_count, "timestamp": timestamp}


@app.get("/results/", response_model=List[schemas.ScrapeResult])
def read_results(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    target_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.ScrapeResult)
    if start_date:
        query = query.filter(models.ScrapeResult.scraped_at >= start_date)
    if end_date:
        query = query.filter(models.ScrapeResult.scraped_at <= end_date)
    if target_id:
        query = query.filter(models.ScrapeResult.target_id == target_id)
    if search:
        like = f"%{search.lower()}%"
        query = query.filter(
            models.ScrapeResult.title.ilike(like)
            | models.ScrapeResult.description.ilike(like)
        )
    return (
        query.order_by(models.ScrapeResult.scraped_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def init_targets(db: Session) -> None:
    """Initialize database with predefined targets if they don't exist."""
    existing_urls = {t.url for t in db.query(models.TargetSite.url).all()}
    new_targets = []
    for url in PREDEFINED_TARGETS:
        if url not in existing_urls:
            new_targets.append(models.TargetSite(url=url, name=url.split('.')[1]))
    if new_targets:
        db.add_all(new_targets)
        db.commit()
        print(f"Added {len(new_targets)} new predefined targets.")


@app.on_event("startup")
def startup_populate():
    db = SessionLocal()
    try:
        init_targets(db)
    finally:
        db.close()
