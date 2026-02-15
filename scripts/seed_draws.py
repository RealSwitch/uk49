"""
Seed script to populate PostgreSQL with sample UK49 draws.

Usage (from project root):
  python scripts/seed_draws.py [num_days]

Examples:
  python scripts/seed_draws.py 60          # Insert 60 days of daily draws
  python scripts/seed_draws.py 30          # Insert 30 days of daily draws
  
With Docker:
  docker-compose exec api python scripts/seed_draws.py 60
"""

import sys
import os
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.models import Base, Draw
from api.database import SessionLocal, DATABASE_URL

def generate_random_draws(num_days=60):
    """Generate sample UK49 draws for the past `num_days` days."""
    draws = []
    today = datetime.now().date()
    
    for i in range(num_days, 0, -1):
        draw_date = (today - timedelta(days=i)).isoformat()
        # UK49 uses numbers 1-49, draw 6 numbers
        numbers = sorted(random.sample(range(1, 50), 6))
        numbers_str = ','.join(map(str, numbers))
        draws.append({
            'draw_date': draw_date,
            'numbers': numbers_str,
        })
    
    return draws

def seed_database(num_days=60):
    """Insert sample draws into the database."""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    
    draws = generate_random_draws(num_days)
    session = SessionLocal()
    
    try:
        # Check if data already exists
        existing_count = session.query(Draw).count()
        if existing_count > 0:
            print(f"✓ Database already has {existing_count} draws. Skipping seed.")
            return
        
        # Insert new draws
        for draw_data in draws:
            draw = Draw(
                draw_date=draw_data['draw_date'],
                numbers=draw_data['numbers'],
            )
            session.add(draw)
        
        session.commit()
        print(f"✓ Successfully inserted {len(draws)} sample draws into the database.")
        print(f"  Date range: {draws[0]['draw_date']} to {draws[-1]['draw_date']}")
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error inserting draws: {e}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == '__main__':
    num_days = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    
    if num_days <= 0 or num_days > 365:
        print("Error: num_days must be between 1 and 365")
        sys.exit(1)
    
    print(f"Seeding {num_days} days of UK49 draws...")
    seed_database(num_days)
