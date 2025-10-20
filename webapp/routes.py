from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from . import models, schemas
from .database import SessionLocal
from scraper import Scraper
from .geocoding import geocode_location
from .utils import haversine_distance
from .security import get_api_key

router = APIRouter(dependencies=[Depends(get_api_key)])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/targets/", response_model=schemas.TargetSite)
def create_target(target: schemas.TargetSiteCreate, db: Session = Depends(get_db)):
    db_target = db.query(models.TargetSite).filter(models.TargetSite.url == target.url).first()
    if db_target:
        raise HTTPException(status_code=400, detail="Target already exists")

    lat, lon = None, None
    if target.name:
        coords = geocode_location(target.name)
        if coords:
            lat, lon = coords

    db_target = models.TargetSite(
        url=target.url,
        name=target.name,
        latitude=lat,
        longitude=lon
    )
    db.add(db_target)
    db.commit()
    db.refresh(db_target)
    return db_target


@router.get("/targets/", response_model=List[schemas.TargetSite])
def read_targets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.TargetSite).offset(skip).limit(limit).all()


from datetime import datetime

def scrape_single_target(target: models.TargetSite, db: Session) -> int:
    """Scrape a single target site using the Scraper class and return the number of new results."""
    keywords = db.query(models.Keyword).all()
    if not keywords:
        # Don't raise an exception, just return 0 results if no keywords are set.
        # This allows the timestamp to still be updated.
        pass

    keyword_list = [k.word for k in keywords]
    scraper_instance = Scraper(keywords=keyword_list)

    site_name = target.name or target.url
    results = scraper_instance.scrape_site(site_name, target.url)

    new_count = 0
    for item in results:
        exists = db.query(models.ScrapeResult).filter_by(url=item['url'], target_id=target.id).first()
        if not exists:
            db_item = models.ScrapeResult(target_id=target.id, **item)
            db.add(db_item)
            new_count += 1

    # Update the last_scraped_at timestamp for the target
    target.last_scraped_at = datetime.utcnow()
    db.add(target)
    db.commit()
    return new_count


@router.post("/scrape")
def scrape_targets(db: Session = Depends(get_db)):
    targets = db.query(models.TargetSite).all()
    if not targets:
        raise HTTPException(status_code=400, detail="No targets configured")
    summary = []
    for target in targets:
        count = scrape_single_target(target, db)
        summary.append({"target_id": target.id, "name": target.name, "new_results": count})
    return {"status": "scrape_complete", "summary": summary}


@router.post("/scrape/{target_id}")
def scrape_target_endpoint(target_id: int, db: Session = Depends(get_db)):
    target = db.get(models.TargetSite, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    new_count = scrape_single_target(target, db)
    timestamp = datetime.utcnow()
    return {"target_id": target_id, "new_results": new_count, "timestamp": timestamp}


@router.get("/results/", response_model=List[schemas.ScrapeResult])
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


@router.delete("/targets/{target_id}")
def delete_target(target_id: int, db: Session = Depends(get_db)):
    target = db.query(models.TargetSite).filter(models.TargetSite.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    db.delete(target)
    db.commit()
    return {"message": f"Target {target_id} deleted"}


@router.post("/keywords/", response_model=schemas.Keyword)
def create_keyword(keyword: schemas.KeywordCreate, db: Session = Depends(get_db)):
    db_keyword = db.query(models.Keyword).filter(models.Keyword.word == keyword.word).first()
    if db_keyword:
        raise HTTPException(status_code=400, detail="Keyword already exists")
    db_keyword = models.Keyword(word=keyword.word)
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword


@router.get("/keywords/", response_model=List[schemas.Keyword])
def read_keywords(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Keyword).offset(skip).limit(limit).all()


@router.delete("/keywords/{keyword_id}")
def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
    keyword = db.query(models.Keyword).filter(models.Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    db.delete(keyword)
    db.commit()
    return {"message": f"Keyword {keyword_id} deleted"}


@router.get("/targets/search-by-radius/", response_model=List[schemas.TargetSite])
def search_targets_by_radius(
    lat: float, lon: float, radius: int, db: Session = Depends(get_db)
):
    """
    Search for targets within a given radius from a central point.
    - lat: Latitude of the center point.
    - lon: Longitude of the center point.
    - radius: Search radius in kilometers.
    """
    all_targets = db.query(models.TargetSite).filter(
        models.TargetSite.latitude.isnot(None),
        models.TargetSite.longitude.isnot(None)
    ).all()

    nearby_targets = []
    for target in all_targets:
        distance = haversine_distance(lat, lon, target.latitude, target.longitude)
        if distance <= radius:
            nearby_targets.append(target)

    return nearby_targets
