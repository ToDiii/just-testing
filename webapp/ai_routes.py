"""
AI analysis routes for the scraper webapp.
"""

from __future__ import annotations
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas
from .database import SessionLocal
from .security import get_api_key
from .ai_service import call_chat_completion, build_analysis_prompt

ai_router = APIRouter(prefix="/ai", dependencies=[Depends(get_api_key)])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Config ──────────────────────────────────────────────────────────────────

@ai_router.get("/config", response_model=schemas.AIConfigResponse | None)
def get_ai_config(db: Session = Depends(get_db)):
    return db.query(models.AIConfig).first()


@ai_router.post("/config", response_model=schemas.AIConfigResponse)
def upsert_ai_config(config: schemas.AIConfigCreate, db: Session = Depends(get_db)):
    existing = db.query(models.AIConfig).first()
    if existing:
        for key, value in config.model_dump().items():
            setattr(existing, key, value if key != "enabled" else (1 if value else 0))
        db.commit()
        db.refresh(existing)
        return existing
    new_cfg = models.AIConfig(
        **{k: v if k != "enabled" else (1 if v else 0) for k, v in config.model_dump().items()}
    )
    db.add(new_cfg)
    db.commit()
    db.refresh(new_cfg)
    return new_cfg


@ai_router.delete("/config")
def delete_ai_config(db: Session = Depends(get_db)):
    db.query(models.AIConfig).delete()
    db.commit()
    return {"message": "AI config deleted"}


# ── Analyze ──────────────────────────────────────────────────────────────────

@ai_router.post("/analyze", response_model=schemas.AIAnalysisResponse)
def analyze_results(request: schemas.AIAnalyzeRequest, db: Session = Depends(get_db)):
    ai_cfg = db.query(models.AIConfig).first()
    if not ai_cfg:
        raise HTTPException(status_code=400, detail="No AI configuration found. Please configure AI in Admin.")
    if not ai_cfg.enabled:
        raise HTTPException(status_code=400, detail="AI analysis is disabled in configuration.")
    if not ai_cfg.api_key:
        raise HTTPException(status_code=400, detail="No API key configured.")

    # Fetch the requested results
    results = (
        db.query(models.ScrapeResult)
        .filter(models.ScrapeResult.id.in_(request.result_ids))
        .all()
    )
    if not results:
        raise HTTPException(status_code=404, detail="No results found for provided IDs.")

    results_dicts = [
        {
            "title": r.title,
            "description": r.description or "",
            "url": r.url,
            "source": r.source,
            "publication_date": r.publication_date or "",
        }
        for r in results
    ]

    messages = build_analysis_prompt(results_dicts, request.mode, ai_cfg.system_prompt)
    prompt_text = json.dumps(messages, ensure_ascii=False)

    # Run async call in sync context
    try:
        result_text = asyncio.run(
            call_chat_completion(
                api_key=ai_cfg.api_key,
                model=ai_cfg.model_name,
                messages=messages,
                base_url=ai_cfg.base_url,
                provider=ai_cfg.provider,
            )
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI API error: {type(e).__name__}: {e}")

    analysis = models.AIAnalysis(
        prompt_used=prompt_text,
        result_text=result_text,
        result_count=len(results),
        target_ids_json=json.dumps(request.result_ids),
        mode=request.mode,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


# ── History ──────────────────────────────────────────────────────────────────

@ai_router.get("/analyses", response_model=list[schemas.AIAnalysisResponse])
def list_analyses(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return (
        db.query(models.AIAnalysis)
        .order_by(models.AIAnalysis.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
