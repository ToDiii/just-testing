from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from . import models, schemas
from .database import SessionLocal
from scraper import Scraper
from .geocoding import geocode_location
from .utils import haversine_distance
from .security import get_api_key
from .notifications import send_notifications

router = APIRouter(dependencies=[Depends(get_api_key)])

@router.get("/scrape/logs", response_model=List[str])
def get_scrape_logs():
    """Retrieve current scrape logs."""
    return Scraper.get_logs()


@router.delete("/scrape/logs")
def clear_scrape_logs():
    """Clear existing scrape logs."""
    Scraper.clear_logs()
    return {"message": "Logs cleared"}

def run_background_scrape(db_session_factory, region_id: Optional[int] = None, target_id: Optional[int] = None, target_ids: Optional[str] = None):
    """Background task to run the scrape."""
    db = db_session_factory()
    state = db.query(models.GlobalState).filter_by(key="global_scrape_status").first()
    if not state:
        state = models.GlobalState(key="global_scrape_status", scrape_status="idle")
        db.add(state)
        db.commit()

    # Reset cancel flag at start
    cancel_flag = db.query(models.GlobalState).filter_by(key="should_cancel_scrape").first()
    if cancel_flag:
        cancel_flag.scrape_status = "0"
        db.commit()

    state.scrape_status = "running"
    state.last_scrape_start = datetime.utcnow()
    db.commit()

    try:
        query = db.query(models.TargetSite)
        if target_ids:
            id_list = [int(i.strip()) for i in target_ids.split(",") if i.strip().isdigit()]
            if id_list:
                query = query.filter(models.TargetSite.id.in_(id_list))
        elif target_id:
            query = query.filter(models.TargetSite.id == target_id)
        elif region_id:
            query = query.filter(models.TargetSite.region_id == region_id)
        
        targets = query.all()
        if not targets:
            Scraper.log(f"No targets found for filter (region_id: {region_id}, target_id: {target_id})")
            state.scrape_status = "idle"
            state.last_scrape_end = datetime.utcnow()
            db.commit()
            return

        Scraper.log(f"Starting scrape for {len(targets)} targets...")
        for i, target in enumerate(targets):
            # Check for cancellation every loop
            db.refresh(state) # Refresh to get latest DB state
            cancel_flag = db.query(models.GlobalState).filter_by(key="should_cancel_scrape").first()
            if cancel_flag and cancel_flag.scrape_status == "1":
                Scraper.log("Scrape cancelled by user.")
                cancel_flag.scrape_status = "0"
                db.commit()
                break

            scrape_single_target(target, db)
            Scraper.log(f"Completed {i+1}/{len(targets)} targets.")
        
        state.scrape_status = "idle"
        state.last_scrape_end = datetime.utcnow()
        db.commit()
    except Exception as e:
        Scraper.log(f"Critical error in background scrape: {e}")
        state.scrape_status = "idle"
        db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/scrape/stop")
def stop_scrape(db: Session = Depends(get_db)):
    """Stop the current background scrape."""
    cancel_flag = db.query(models.GlobalState).filter_by(key="should_cancel_scrape").first()
    if not cancel_flag:
        cancel_flag = models.GlobalState(key="should_cancel_scrape", scrape_status="1")
        db.add(cancel_flag)
    else:
        cancel_flag.scrape_status = "1"
    db.commit()
    return {"message": "Cancellation requested"}


@router.post("/targets", response_model=schemas.TargetSite)
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


@router.get("/targets", response_model=List[schemas.TargetSite])
def read_targets(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.TargetSite).offset(skip).limit(limit).all()


def get_or_create_global_state(db: Session) -> models.GlobalState:
    """Helper to get the global state object, creating it if it doesn't exist."""
    state = db.query(models.GlobalState).filter_by(key="global_scrape_status").first()
    if not state:
        state = models.GlobalState(key="global_scrape_status", scrape_status="idle")
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


@router.get("/scrape/status", response_model=schemas.GlobalState)
def get_scrape_status(db: Session = Depends(get_db)):
    """Get the current status of the global scraper."""
    return get_or_create_global_state(db)


from datetime import datetime

def scrape_single_target(target: models.TargetSite, db: Session) -> int:
    """Scrape a single target site using the Scraper class and return the number of new results."""
    keywords = db.query(models.Keyword).all()
    if not keywords:
        # Don't raise an exception, just return 0 results if no keywords are set.
        # This allows the timestamp to still be updated.
        pass

    keyword_list = [{"word": k.word, "category_id": k.category_id} for k in keywords]
    
    # Fetch global scraping config
    config = db.query(models.ScrapingConfig).first()
    if not config:
        # Default values if no config exists
        scraper_instance = Scraper(keywords=keyword_list)
    else:
        scraper_instance = Scraper(
            keywords=keyword_list,
            max_html_links=config.max_html_links,
            max_pdf_links=config.max_pdf_links,
            delay=config.request_delay
        )

    site_name = target.name or target.url
    results = scraper_instance.scrape_site(site_name, target.url)

    new_count = 0
    new_items = []
    for item in results:
        exists = db.query(models.ScrapeResult).filter_by(url=item['url'], target_id=target.id).first()
        if not exists:
            db_item = models.ScrapeResult(target_id=target.id, **item)
            db.add(db_item)
            new_count += 1
            new_items.append(item)
    
    if new_items:
        try:
            send_notifications(new_items, db)
        except Exception as e:
            print(f"Error sending notifications: {e}")

    # Update the last_scraped_at timestamp for the target
    target.last_scraped_at = datetime.utcnow()
    db.add(target)
    db.commit()
    return new_count


@router.post("/scrape")
def trigger_scrape(
    background_tasks: BackgroundTasks,
    region_id: Optional[int] = None,
    target_id: Optional[int] = None,
    target_ids: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Trigger a scrape operation in the background.
    - region_id: Optional filter for a specific region.
    - target_id: Optional filter for a specific target.
    - target_ids: Optional comma-separated list of target IDs.
    """
    state = get_or_create_global_state(db)
    if state.scrape_status == "running":
        raise HTTPException(status_code=409, detail="A scrape is already in progress.")
    
    # Clear logs before starting
    Scraper.clear_logs()
    
    # We pass the SessionLocal factory because background tasks need their own session
    background_tasks.add_task(run_background_scrape, SessionLocal, region_id, target_id, target_ids)

    return {"message": "Scrape started in background"}


@router.post("/scrape/{target_id}")
def scrape_target_endpoint(target_id: int, db: Session = Depends(get_db)):
    target = db.get(models.TargetSite, target_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    new_count = scrape_single_target(target, db)
    timestamp = datetime.utcnow()
    return {"target_id": target_id, "new_results": new_count, "timestamp": timestamp}


@router.get("/results", response_model=List[schemas.ScrapeResult])
def read_results(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    target_id: Optional[int] = None,
    target_ids: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.ScrapeResult).filter(models.ScrapeResult.is_ignored == 0)
    if start_date:
        query = query.filter(models.ScrapeResult.scraped_at >= start_date)
    if end_date:
        query = query.filter(models.ScrapeResult.scraped_at <= end_date)
    if target_id:
        query = query.filter(models.ScrapeResult.target_id == target_id)
    if target_ids:
        id_list = [int(i.strip()) for i in target_ids.split(",") if i.strip().isdigit()]
        if id_list:
            query = query.filter(models.ScrapeResult.target_id.in_(id_list))
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


@router.post("/results/bulk-ignore")
def bulk_ignore_results(result_ids: List[int], db: Session = Depends(get_db)):
    """Mark multiple results as ignored (deleted from UI but kept in DB to avoid re-scrape)."""
    db.query(models.ScrapeResult).filter(models.ScrapeResult.id.in_(result_ids)).update(
        {"is_ignored": 1}, synchronize_session=False
    )
    db.commit()
    return {"message": f"Ignored {len(result_ids)} results"}


@router.delete("/targets/{target_id}")
def delete_target(target_id: int, db: Session = Depends(get_db)):
    target = db.query(models.TargetSite).filter(models.TargetSite.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    db.delete(target)
    db.commit()
    return {"message": f"Target {target_id} deleted"}


@router.post("/keywords", response_model=schemas.Keyword)
def create_keyword(keyword: schemas.KeywordCreate, db: Session = Depends(get_db)):
    db_keyword = db.query(models.Keyword).filter(models.Keyword.word == keyword.word).first()
    if db_keyword:
        raise HTTPException(status_code=400, detail="Keyword already exists")
    db_keyword = models.Keyword(word=keyword.word, category_id=keyword.category_id)
    db.add(db_keyword)
    db.commit()
    db.refresh(db_keyword)
    return db_keyword


@router.get("/keywords", response_model=List[schemas.Keyword])
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


@router.post("/categories", response_model=schemas.Category)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    db_category = db.query(models.Category).filter(models.Category.name == category.name).first()
    if db_category:
        raise HTTPException(status_code=400, detail="Category already exists")
    db_category = models.Category(name=category.name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.get("/categories", response_model=List[schemas.Category])
def read_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Category).offset(skip).limit(limit).all()


@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"message": f"Category {category_id} deleted"}


@router.get("/targets/search-by-radius", response_model=List[schemas.TargetSite])
def search_targets_by_radius(
    lat: float, lon: float, radius: float, db: Session = Depends(get_db)
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


@router.get("/regions", response_model=List[schemas.Region])
def read_regions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Region).offset(skip).limit(limit).all()


@router.post("/regions", response_model=schemas.Region)
def create_region(region: schemas.RegionCreate, db: Session = Depends(get_db)):
    db_region = models.Region(**region.dict())
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return db_region


@router.delete("/regions/{region_id}")
def delete_region(region_id: int, db: Session = Depends(get_db)):
    region = db.query(models.Region).filter(models.Region.id == region_id).first()
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    db.delete(region)
    db.commit()
    return {"message": f"Region {region_id} deleted"}


@router.post("/notifications/config", response_model=schemas.NotificationConfig)
def create_notification_config(config: schemas.NotificationConfigCreate, db: Session = Depends(get_db)):
    db_config = models.NotificationConfig(**config.dict())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


@router.get("/notifications/config", response_model=List[schemas.NotificationConfig])
def read_notification_configs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.NotificationConfig).offset(skip).limit(limit).all()


@router.delete("/notifications/config/{config_id}")
def delete_notification_config(config_id: int, db: Session = Depends(get_db)):
    config = db.query(models.NotificationConfig).filter(models.NotificationConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    db.delete(config)
    db.commit()
    return {"message": f"Configuration {config_id} deleted"}


@router.post("/notifications/test/{config_id}")
def test_notification_endpoint(config_id: int, db: Session = Depends(get_db)):
    """Trigger a test notification for a specific configuration."""
    from .notifications import send_test_notification
    try:
        send_test_notification(config_id, db)
        return {"message": "Test notification sent successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send test notification: {str(e)}")


@router.get("/config/scraping", response_model=schemas.ScrapingConfig)
def get_scraping_config(db: Session = Depends(get_db)):
    config = db.query(models.ScrapingConfig).first()
    if not config:
        # Create default config if it doesn't exist
        config = models.ScrapingConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.post("/config/scraping", response_model=schemas.ScrapingConfig)
def update_scraping_config(config_in: schemas.ScrapingConfigCreate, db: Session = Depends(get_db)):
    config = db.query(models.ScrapingConfig).first()
    if not config:
        config = models.ScrapingConfig(**config_in.dict())
        db.add(config)
    else:
        for var, value in config_in.dict().items():
            setattr(config, var, value)
    db.commit()
    db.refresh(config)
    return config

