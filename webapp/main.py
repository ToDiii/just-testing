from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from . import models, schemas
from .database import SessionLocal, engine

import scraper

templates = Jinja2Templates(directory="webapp/templates")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Scraper Web API")
if os.path.isdir("webapp/static"):
    app.mount("/static", StaticFiles(directory="webapp/static"), name="static")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


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
    """Scrape a single target site and return number of new results"""
    new_count = 0
    html = scraper.fetch_html(target.url)
    if not html:
        return new_count
    html_links, pdf_links = scraper.find_relevant_links(html, target.url)
    for link in html_links:
        page_html = scraper.fetch_html(link)
        if not page_html:
            continue
        items = scraper.extract_data_from_html_page(
            link, page_html, target.name or target.url
        )
        for item in items:
            result = models.ScrapeResult(target_id=target.id, **item)
            db.add(result)
            new_count += 1
    for link in pdf_links:
        pdf_text = scraper.download_pdf_to_text(link)
        if not pdf_text:
            continue
        items = scraper.extract_data_from_pdf_text(
            link, pdf_text, target.name or target.url
        )
        for item in items:
            result = models.ScrapeResult(target_id=target.id, **item)
            db.add(result)
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
        summary.append({"target_id": target.id, "new_results": count})
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
    new_targets = []
    for url in scraper.PREDEFINED_TARGETS:
        if not db.query(models.TargetSite).filter(models.TargetSite.url == url).first():
            new_targets.append(models.TargetSite(url=url))
    if new_targets:
        db.add_all(new_targets)
        db.commit()
        for target in new_targets:
            print(f"Added target URL: {target.url}")


@app.on_event("startup")
def startup_populate():
    db = SessionLocal()
    try:
        init_targets(db)
    finally:
        db.close()
