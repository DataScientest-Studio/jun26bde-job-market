"""Shared application settings."""

from pathlib import Path

FASTAPI_URL = "http://127.0.0.1:8000"

FRONTEND_PORT = 8050

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "data"

RAW_DATA_DIRECTORY = DATA_DIRECTORY / "raw" / "arbeitsagentur"
DATABASE_PATH = DATA_DIRECTORY / "processed" / "job_market.sqlite3"


KEYWORDS = ("Data Engineer", "Data Analyst")
FIRST_PAGE = 1
NUMBER_OF_PAGES = 3
JOBS_PER_PAGE = 50
