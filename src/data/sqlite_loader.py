"""Load cleaned Arbeitsagentur job data into SQLite."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

# region Constants

DATA_DIRECTORY = Path(__file__).resolve().parent
DEFAULT_DATABASE_PATH = DATA_DIRECTORY / "processed" / "job_market.sqlite3"

# endregion


# region SQL statements

CREATE_JOBS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    reference_number TEXT PRIMARY KEY,
    title TEXT,
    occupation TEXT,
    company TEXT,
    description TEXT,
    offer_type TEXT,
    full_time INTEGER,
    contract_duration TEXT,
    career_change_suitable INTEGER,
    home_office_possible INTEGER,
    temporary_employment INTEGER,
    private_placement INTEGER,
    salary_period TEXT,
    salary_type TEXT,
    salary_min REAL,
    salary_max REAL,
    entry_date TEXT,
    publication_date TEXT,
    first_publication_date TEXT,
    modified_at TEXT,
    external_url TEXT,
    partner_name TEXT,
    partner_url TEXT,
    employer_customer_hash TEXT
);
"""


CREATE_JOB_LOCATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS job_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_number TEXT NOT NULL,
    postal_code TEXT,
    city TEXT,
    region TEXT,
    country TEXT,
    latitude REAL,
    longitude REAL,
    FOREIGN KEY (reference_number)
        REFERENCES jobs (reference_number)
        ON DELETE CASCADE
);
"""


CREATE_LOCATION_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_job_locations_reference_number
ON job_locations (reference_number);
"""


UPSERT_JOB_SQL = """
INSERT INTO jobs (
    reference_number,
    title,
    occupation,
    company,
    description,
    offer_type,
    full_time,
    contract_duration,
    career_change_suitable,
    home_office_possible,
    temporary_employment,
    private_placement,
    salary_period,
    salary_type,
    salary_min,
    salary_max,
    entry_date,
    publication_date,
    first_publication_date,
    modified_at,
    external_url,
    partner_name,
    partner_url,
    employer_customer_hash
)
VALUES (
    :reference_number,
    :title,
    :occupation,
    :company,
    :description,
    :offer_type,
    :full_time,
    :contract_duration,
    :career_change_suitable,
    :home_office_possible,
    :temporary_employment,
    :private_placement,
    :salary_period,
    :salary_type,
    :salary_min,
    :salary_max,
    :entry_date,
    :publication_date,
    :first_publication_date,
    :modified_at,
    :external_url,
    :partner_name,
    :partner_url,
    :employer_customer_hash
)
ON CONFLICT(reference_number) DO UPDATE SET
    title = excluded.title,
    occupation = excluded.occupation,
    company = excluded.company,
    description = excluded.description,
    offer_type = excluded.offer_type,
    full_time = excluded.full_time,
    contract_duration = excluded.contract_duration,
    career_change_suitable = excluded.career_change_suitable,
    home_office_possible = excluded.home_office_possible,
    temporary_employment = excluded.temporary_employment,
    private_placement = excluded.private_placement,
    salary_period = excluded.salary_period,
    salary_type = excluded.salary_type,
    salary_min = excluded.salary_min,
    salary_max = excluded.salary_max,
    entry_date = excluded.entry_date,
    publication_date = excluded.publication_date,
    first_publication_date = excluded.first_publication_date,
    modified_at = excluded.modified_at,
    external_url = excluded.external_url,
    partner_name = excluded.partner_name,
    partner_url = excluded.partner_url,
    employer_customer_hash = excluded.employer_customer_hash;
"""


INSERT_LOCATION_SQL = """
INSERT INTO job_locations (
    reference_number,
    postal_code,
    city,
    region,
    country,
    latitude,
    longitude
)
VALUES (
    :reference_number,
    :postal_code,
    :city,
    :region,
    :country,
    :latitude,
    :longitude
);
"""


BOOLEAN_FIELDS = {
    "full_time",
    "career_change_suitable",
    "home_office_possible",
    "temporary_employment",
    "private_placement",
}

# endregion


# region Helper functions


def to_sqlite_boolean(value: Any) -> int | None:
    """Convert a JSON boolean into SQLite's integer representation."""

    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    raise ValueError(f"Expected a boolean or null, received {value!r}")


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description="Load clean Arbeitsagentur jobs into SQLite."
    )

    parser.add_argument(
        "source",
        type=Path,
        help="Path to a clean-jobs.json file.",
    )

    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help=("Path to the SQLite database. " f"Default: {DEFAULT_DATABASE_PATH}"),
    )

    return parser.parse_args()


# endregion


def load_json(source_path: Path) -> list[dict[str, Any]]:
    """Read and validate a clean-jobs JSON file."""

    with source_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError("Expected the JSON file to contain a list of jobs")

    jobs: list[dict[str, Any]] = []

    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Job {index} is not a JSON object")

        jobs.append(item)

    return jobs


def prepare_job(job: dict[str, Any]) -> dict[str, Any]:
    """Prepare one cleaned job for insertion into SQLite."""

    reference_number = job.get("reference_number")

    if not isinstance(reference_number, str) or not reference_number:
        raise ValueError("Job is missing a valid reference_number")

    # Exclude locations because they are stored separately in the job_locations table.
    prepared_job = {key: value for key, value in job.items() if key != "locations"}

    for field in BOOLEAN_FIELDS:
        prepared_job[field] = to_sqlite_boolean(job.get(field))

    return prepared_job


def create_schema(connection: sqlite3.Connection) -> None:
    """Create the database tables and indexes."""

    connection.execute(CREATE_JOBS_TABLE_SQL)
    connection.execute(CREATE_JOB_LOCATIONS_TABLE_SQL)
    connection.execute(CREATE_LOCATION_INDEX_SQL)


def load_jobs(
    connection: sqlite3.Connection,
    jobs: list[dict[str, Any]],
) -> tuple[int, int]:
    """Insert or update jobs and replace their locations."""

    num_loaded_jobs = 0
    num_skipped_jobs = 0

    for job_number, job in enumerate(jobs, start=1):
        try:
            prepared_job = prepare_job(job)
            reference_number = prepared_job["reference_number"]

            connection.execute(UPSERT_JOB_SQL, prepared_job)

            # Locations in the current JSON file replace previously stored ones.
            connection.execute(
                """
                DELETE FROM job_locations
                WHERE reference_number = ?
                """,
                (reference_number,),
            )

            locations = job.get("locations", [])

            if locations is None:
                locations = []

            if not isinstance(locations, list):
                raise ValueError("'locations' must be a list")

            for location in locations:
                if not isinstance(location, dict):
                    raise ValueError("Each location must be a JSON object")

                connection.execute(
                    INSERT_LOCATION_SQL,
                    {
                        "reference_number": reference_number,
                        "postal_code": location.get("postal_code"),
                        "city": location.get("city"),
                        "region": location.get("region"),
                        "country": location.get("country"),
                        "latitude": location.get("latitude"),
                        "longitude": location.get("longitude"),
                    },
                )

            num_loaded_jobs += 1

        except (ValueError, sqlite3.Error) as error:
            num_skipped_jobs += 1
            print(f"Skipping job {job_number}: {error}")

    return num_loaded_jobs, num_skipped_jobs


def load_clean_jobs_to_sqlite(
    jobs: list[dict[str, Any]],
    database_path: Path = DEFAULT_DATABASE_PATH,
) -> tuple[int, int]:
    """Create the SQLite database and load cleaned jobs into it."""

    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        create_schema(connection)

        num_loaded_jobs, num_skipped_jobs = load_jobs(
            connection=connection,
            jobs=jobs,
        )

    return num_loaded_jobs, num_skipped_jobs


def main() -> None:
    """Load a clean-jobs JSON file into SQLite."""

    arguments = parse_arguments()

    source_path: Path = arguments.source
    database_path: Path = arguments.database

    if not source_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {source_path}")

    database_path.parent.mkdir(parents=True, exist_ok=True)

    jobs = load_json(source_path)

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        create_schema(connection)

        loaded_jobs, skipped_jobs = load_jobs(connection, jobs)

    print(f"Source file: {source_path}")
    print(f"Database: {database_path}")
    print(f"Loaded jobs: {loaded_jobs}")
    print(f"Skipped jobs: {skipped_jobs}")


if __name__ == "__main__":
    main()
