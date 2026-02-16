"""
Fallback: Sample UK49 Drivetime draw generator.

Generates realistic UK49 draws from the past 90 days.
Use this when the live scraper doesn't work.

Usage:
  docker-compose exec api python scripts/generate_sample_data.py [num_days]

Examples:
  docker-compose exec api python scripts/generate_sample_data.py 90
  docker-compose exec api python scripts/generate_sample_data.py 60
"""

import sys
import os
import random
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.database import SessionLocal, engine
from api.models import Base, Draw

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DRAWS = [
    # Real or realistic-looking UK49 Teatime draws (sample)
    "2,5,9,15,28,31",
    "3,7,11,18,25,42",
    "1,6,12,19,24,37",
    "4,8,14,21,33,44",
    "2,10,16,27,35,48",
    "5,9,13,20,29,41",
    "3,11,17,26,34,46",
    "1,7,15,22,30,39",
    "4,12,18,28,36,49",
    "6,14,23,32,43,47",
    "2,8,19,25,38,45",
    "5,11,20,29,40,48",
    "3,13,21,31,37,44",
    "1,9,17,24,33,42",
    "4,10,22,27,35,46",
    "6,15,26,34,41,49",
    "2,7,16,30,39,47",
    "5,12,18,28,36,43",
    "3,14,19,32,38,45",
    "1,11,23,29,37,40",
]


def generate_sample_draws(num_days=90):
    """Generate sample UK49 draws for the past `num_days` days.

    Draws are realistic but randomly generated (not actual historical data).
    """
    draws = []
    today = datetime.now().date()

    for i in range(num_days, 0, -1):
        draw_date = (today - timedelta(days=i)).isoformat()
        # Pick a base draw and randomly vary it slightly
        base = random.choice(BASE_DRAWS)
        base_nums = [int(x) for x in base.split(',')]

        # Randomly swap 0-2 numbers
        nums = base_nums.copy()
        for _ in range(random.randint(0, 2)):
            idx = random.randint(0, 5)
            nums[idx] = random.randint(1, 49)

        nums = sorted(set(nums))[:6]
        while len(nums) < 6:
            nums.append(random.randint(1, 49))
        nums = sorted(set(nums))[:6]

        draws.append({'draw_date': draw_date, 'numbers': ','.join(map(str, nums))})

    return draws


def main(num_days=90):
    """Generate and insert sample draws into the database."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        existing_count = session.query(Draw).count()
        if existing_count > 0:
            logger.info(
                f"✓ Database already has {existing_count} draws. Skipping generation."
            )
            return

        logger.info(f"Generating {num_days} days of sample UK49 draws...")
        draws_data = generate_sample_draws(num_days)

        for data in draws_data:
            draw = Draw(draw_date=data['draw_date'], numbers=data['numbers'])
            session.add(draw)

        session.commit()
        logger.info(f"✓ Successfully inserted {len(draws_data)} sample draws")
        logger.info(f"  Date range: {draws_data[0]['draw_date']} to {draws_data[-1]['draw_date']}")

    except Exception as e:
        session.rollback()
        logger.exception(f"✗ Error: {e}")
        sys.exit(1)
    finally:
        session.close()


if __name__ == '__main__':
    num_days = int(sys.argv[1]) if len(sys.argv) > 1 else 90

    if num_days <= 0 or num_days > 365:
        logger.error('num_days must be between 1 and 365')
        sys.exit(1)

    main(num_days)
