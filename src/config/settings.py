"""Shared application settings."""

from pathlib import Path

SRC_DIRECTORY = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = SRC_DIRECTORY / "data"
DATABASE_PATH = DATA_DIRECTORY / "processed" / "job_market.sqlite3"
