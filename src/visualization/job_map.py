"""Build an HTML map of job locations."""

from html import escape

import folium
import pandas as pd

from src.data.sqlite_database import get_database_connection

GET_JOB_COORDINATES_SQL = """
SELECT
    jobs.reference_number,
    jobs.title,
    jobs.company,
    job_locations.city,
    job_locations.latitude,
    job_locations.longitude
FROM job_locations
JOIN jobs USING (reference_number)
WHERE job_locations.latitude IS NOT NULL
  AND job_locations.longitude IS NOT NULL
"""

INITIAL_MAP_ZOOM = 6


def _escape_value(value: object, fallback: str) -> str:
    if pd.isna(value):
        return fallback

    return escape(str(value))


def _load_job_coordinates() -> pd.DataFrame:
    with get_database_connection() as connection:
        return pd.read_sql_query(GET_JOB_COORDINATES_SQL, connection)


def _build_job_map(data: pd.DataFrame) -> folium.Map:
    if data.empty:
        raise ValueError("No job locations with coordinates were found.")

    job_map = folium.Map(
        location=[
            data["latitude"].mean(),
            data["longitude"].mean(),
        ],
        zoom_start=INITIAL_MAP_ZOOM,
    )

    for row in data.itertuples(index=False):
        title = _escape_value(row.title, "Unknown title")
        company = _escape_value(row.company, "Unknown company")
        city = _escape_value(row.city, "Unknown city")

        popup_html = f"<strong>{title}</strong><br>" f"{company}<br>" f"{city}"

        folium.Marker(
            location=[row.latitude, row.longitude],
            popup=folium.Popup(popup_html, max_width=300),
        ).add_to(job_map)

    return job_map


def build_job_map_html() -> str:
    data = _load_job_coordinates()
    job_map = _build_job_map(data)
    return job_map.get_root().render()
