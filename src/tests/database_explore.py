import sqlite3

db = "src/data/processed/job_market.sqlite3"
table = "job_locations"

with sqlite3.connect(db) as conn:
    cur = conn.cursor()
    cur.execute(f"""
        SELECT country,
               COUNT(*) AS n_rows
        FROM {table}
        WHERE latitude IS NULL
          AND longitude IS NULL
        GROUP BY country
    """)
    cities_with_coords = cur.fetchall()


print("rows_without_coords:", cities_with_coords)
