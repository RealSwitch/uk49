from typing import Optional, Dict, List
from sqlalchemy import text
from sqlalchemy.engine import Engine


def get_rolling_frequency(engine: Engine, target_date: Optional[str] = None) -> Dict:
    """Return rolling 30-day frequency per number for a given date.

    This function encapsulates SQL logic so the API layer doesn't contain
    raw SQL or DB connection handling.
    """
    with engine.connect() as conn:
        if not target_date:
            res = conn.execute(text("SELECT MAX(draw_date::date) FROM draws"))
            max_date = res.scalar()
            if max_date is None:
                return {"draw_date": None, "frequencies": []}
            target_date = str(max_date)

        sql = text(
            """
WITH exploded AS (
  SELECT
    id,
    draw_date::date AS draw_date,
    (regexp_split_to_table(numbers, E'\\s*,\\s*'))::int AS number
  FROM draws
),
target AS (
  SELECT CAST(:target_date AS date) AS draw_date
)
SELECT
  gs.number,
  COUNT(e.*) AS freq_30d
FROM target t
CROSS JOIN (SELECT generate_series(1,49) AS number) gs
LEFT JOIN exploded e
  ON e.number = gs.number
  AND e.draw_date BETWEEN t.draw_date - INTERVAL '29 days' AND t.draw_date
GROUP BY gs.number
ORDER BY gs.number;
"""
        )

        result = conn.execute(sql, {"target_date": target_date})
        rows: List[Dict] = [{"number": int(r[0]), "freq_30d": int(r[1])} for r in result.fetchall()]

    return {"draw_date": target_date, "frequencies": rows}
