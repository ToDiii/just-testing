from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from . import models, schemas
from .database import SessionLocal, engine
from .routes import router as api_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Scraper Web API", docs_url="/api/docs", openapi_url="/api/openapi.json")

# API router
app.include_router(api_router, prefix="/api")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db(db: Session) -> None:
    """Initialize database with predefined keywords if they don't exist."""
    existing_keywords = {k.word for k in db.query(models.Keyword).all()}
    default_keywords = [
        "baugebiet", "bebauungsplan", "flächennutzungsplan", "grundstück",
        "bauplatz", "bauland", "ausschreibung", "verkauf", "entwicklung",
        "neubaugebiet", "sanierung"
    ]
    new_keywords = []
    for word in default_keywords:
        if word not in existing_keywords:
            new_keywords.append(models.Keyword(word=word))

    if new_keywords:
        db.add_all(new_keywords)
        db.commit()
        print(f"Added {len(new_keywords)} new predefined keywords.")

@app.on_event("startup")
def startup_populate():
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()

# Serve Svelte app
if os.path.exists("dist"):
    app.mount("/", StaticFiles(directory="dist", html=True), name="static")

@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    return FileResponse('dist/index.html')
