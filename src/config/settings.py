"""Shared application settings."""

import os
from pathlib import Path

FASTAPI_URL = "http://127.0.0.1:8000"

FRONTEND_PORT = 8050

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "data"

RAW_DATA_DIRECTORY = DATA_DIRECTORY / "raw" / "arbeitsagentur"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://job_market:job_market@localhost:5432/job_market",
)


KEYWORDS = ("Data Engineer", "Data Analyst")
FIRST_PAGE = 1
NUMBER_OF_PAGES = 3
JOBS_PER_PAGE = 50
