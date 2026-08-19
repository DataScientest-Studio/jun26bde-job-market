"""Shared application settings."""

import os
from pathlib import Path

FASTAPI_URL = os.getenv(
    "FASTAPI_URL",
    "http://127.0.0.1:8000",
)

FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "8050"))

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "data"

RAW_DATA_DIRECTORY = DATA_DIRECTORY / "raw" / "arbeitsagentur"
PROCESSED_DATA_DIRECTORY = DATA_DIRECTORY / "processed" / "arbeitsagentur"

CLEAN_JSON_FILE_NAME = "clean-jobs.json"
JOB_DETAILS_FILE_NAME = "job-details.json"
JOB_DETAIL_FAILURES_FILE_NAME = "job-detail-failures.json"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://job_market:job_market@localhost:5432/job_market",
)

PUSHGATEWAY_URL = os.getenv(
    "PUSHGATEWAY_URL",
    "http://127.0.0.1:9091",
)

DASH_DEBUG = os.getenv("DASH_DEBUG", "true").lower() == "true"

# Arbeitsagentur API / ETL
DEFAULT_JOB_SEARCH_KEYWORDS = ("Data Engineer", "Data Analyst")
API_START_PAGE = 1
API_REQUEST_PAGE_SIZE = 50
NUM_API_REQUESTS_PER_SEARCH = 3


# Dashboard
JOBS_PAGE_SIZE = 20
