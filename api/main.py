import os
import random
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from .stats import get_rolling_frequency

from .database import SessionLocal, engine
from .models import Base, Draw

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)

app = FastAPI(title='UK49 API')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/health')
def health():
    return {'status': 'ok'}


@app.get('/draws')
def list_draws(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(Draw).order_by(Draw.id.desc()).limit(limit).all()
    return [{'id': r.id, 'draw_date': r.draw_date, 'draw_type': r.draw_type, 'numbers': r.numbers} for r in rows]


@app.get('/stats/rolling_frequency')
def rolling_frequency(target_date: Optional[str] = None):
    """Proxy endpoint that uses `api.stats.get_rolling_frequency`.

    Keeps SQL and DB logic inside `api.stats`.
    Returns empty frequencies if no data available.
    """
    result = get_rolling_frequency(engine, target_date)
    return result


@app.get('/stats/hot_numbers')
def hot_numbers(target_date: Optional[str] = None, top_n: int = 10):
    """Return the top `top_n` hot numbers based on 30-day rolling frequency.

    - `target_date`: optional date to compute the window for (YYYY-MM-DD). If omitted uses latest draw_date.
    - `top_n`: how many top numbers to return (1..49).
    
    Returns empty list if no draws available.
    """
    if top_n <= 0 or top_n > 49:
        raise HTTPException(status_code=400, detail='top_n must be between 1 and 49')

    result = get_rolling_frequency(engine, target_date)
    freqs = result.get('frequencies', [])
    
    if not freqs:
        # No data available, return empty result
        return {"draw_date": result.get('draw_date'), "top_n": top_n, "hot_numbers": []}

    # sort by frequency desc, then number asc for deterministic ordering
    sorted_freqs = sorted(freqs, key=lambda r: (-r['freq_30d'], r['number']))
    top = sorted_freqs[:top_n]

    return {"draw_date": result['draw_date'], "top_n": top_n, "hot_numbers": top}


@app.post('/admin/seed')
def seed_draws(num_days: int = 60, db: Session = Depends(get_db)):
    """Seed the database with random UK49 draws for testing.
    
    - `num_days`: number of days of draws to generate (1-365).
    
    Only seeds if the database is empty.
    """
    if num_days <= 0 or num_days > 365:
        raise HTTPException(status_code=400, detail='num_days must be between 1 and 365')
    
    existing_count = db.query(Draw).count()
    if existing_count > 0:
        return {"message": f"Database already has {existing_count} draws. Skipping seed."}
    
    today = datetime.now().date()
    draws_to_insert = []
    
    for i in range(num_days, 0, -1):
        draw_date = (today - timedelta(days=i)).isoformat()
        # Generate both lunchtime and teatime draws for each day
        for draw_type in ['lunchtime', 'teatime']:
            # Generate 6 random numbers from 1-49
            numbers = sorted(random.sample(range(1, 50), 6))
            numbers_str = ','.join(map(str, numbers))
            
            draw = Draw(draw_date=draw_date, draw_type=draw_type, numbers=numbers_str)
            draws_to_insert.append(draw)
    
    db.add_all(draws_to_insert)
    db.commit()
    
    return {
        "message": f"Successfully seeded {len(draws_to_insert)} draws",
        "date_range": f"{draws_to_insert[0].draw_date} to {draws_to_insert[-1].draw_date}"
    }


@app.post('/admin/scrape')
def scrape_now():
    """Run the UK49 scraper immediately and load results into the database.
    
    This endpoint triggers the ETL pipeline to:
    1. Fetch real UK49 results from https://uk49s.net/
    2. Transform and validate the data
    3. Load into PostgreSQL
    
    Note: This may take a few seconds.
    """
    try:
        logger.info("Scraper endpoint triggered: fetching from https://uk49s.net/")
        # Dynamically load ETL from the local script file to avoid importing
        # the installed `airflow` package which triggers heavy initialization.
        import importlib.util
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        etl_path = os.path.join(repo_root, 'airflow', 'scripts', 'etl_tasks.py')
        if not os.path.exists(etl_path):
            raise HTTPException(status_code=500, detail=f'etl_tasks.py not found at {etl_path}')
        spec = importlib.util.spec_from_file_location('uk49_etl_tasks', etl_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        etl = getattr(mod, 'etl')
        etl()
        logger.info("Scraper completed successfully")
        return {"message": "Scraper completed successfully. Check /stats endpoints."}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Scraper failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scraper failed: {str(e)}")
