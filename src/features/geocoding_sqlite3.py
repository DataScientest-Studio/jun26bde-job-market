import sqlite3
import time
from geopy.geocoders import Nominatim

db = "src/data/processed/job_market.sqlite3"
table = "job_locations"

geolocator = Nominatim(user_agent="job-market-mapper")


def geocode_location(postal_code=None, city=None, country=None):
    if not any([postal_code, city, country]):
        return None, None

    query_parts = []
    if postal_code:
        query_parts.append(str(postal_code).strip())
    if city:
        query_parts.append(str(city).strip())
    if country:
        query_parts.append(str(country).strip())

    query = ", ".join(query_parts)

    try:
        location = geolocator.geocode(query, exactly_one=True)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        print(f"Geocoding failed for '{query}': {e}")

    return None, None


with sqlite3.connect(db) as conn:
    cur = conn.cursor()
    cur.execute(f"""
        SELECT id, postal_code, city, country
        FROM {table}
        WHERE (latitude IS NULL OR longitude IS NULL)
          AND (
                postal_code IS NOT NULL
                OR city IS NOT NULL
              )
          AND country IS NOT NULL
    """)
    rows = cur.fetchall()

    for row_id, postal_code, city, country in rows:
        lat, lon = geocode_location(postal_code, city, country)
        time.sleep(1)

        if lat is not None and lon is not None:
            cur.execute(f"""
                UPDATE {table}
                SET latitude = ?, longitude = ?
                WHERE id = ?
            """, (lat, lon, row_id))

    conn.commit()


def main() -> None:

if __name__ == "__main__":
    main()