from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas
from .database import SessionLocal, engine

import scraper

templates = Jinja2Templates(directory="webapp/templates")

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Scraper Web API")
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


@app.post("/scrape")
def scrape_targets(db: Session = Depends(get_db)):
    targets = db.query(models.TargetSite).all()
    if not targets:
        raise HTTPException(status_code=400, detail="No targets configured")
    for target in targets:
        html = scraper.fetch_html(target.url)
        if not html:
            continue
        html_links, pdf_links = scraper.find_relevant_links(html, target.url)
        for link in html_links:
            page_html = scraper.fetch_html(link)
            if not page_html:
                continue
            items = scraper.extract_data_from_html_page(link, page_html, target.name or target.url)
            for item in items:
                result = models.ScrapeResult(target_id=target.id, **item)
                db.add(result)
        for link in pdf_links:
            pdf_text = scraper.download_pdf_to_text(link)
            if not pdf_text:
                continue
            items = scraper.extract_data_from_pdf_text(link, pdf_text, target.name or target.url)
            for item in items:
                result = models.ScrapeResult(target_id=target.id, **item)
                db.add(result)
        db.commit()
    return {"status": "scrape_complete"}


@app.get("/results/", response_model=List[schemas.ScrapeResult])
def read_results(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.ScrapeResult).order_by(models.ScrapeResult.scraped_at.desc()).offset(skip).limit(limit).all()
