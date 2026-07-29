"""
API routes for reading job advertisements from the processed SQLite database.

The endpoints in this module provide read-only access to jobs previously
collected and processed by the data pipeline.
"""

import logging
from pathlib import Path
import sqlite3

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

# region Setup

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)

# endregion


# region Constants

DATABASE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "processed" / "job_market.sqlite3"
)

# endregion


# region SQL queries

GET_JOBS_SQL = """
SELECT
    reference_number,
    title,
    company,
    occupation
FROM jobs
ORDER BY publication_date DESC
LIMIT ? OFFSET ?
"""

GET_SINGLE_JOB_SQL = """
SELECT
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
FROM jobs
WHERE reference_number = ?
"""

GET_JOB_LOCATIONS_SQL = """
SELECT
    postal_code,
    city,
    region,
    country,
    latitude,
    longitude
FROM job_locations
WHERE reference_number = ?
ORDER BY id
"""

# endregion


# region Response models


class JobResponse(BaseModel):
    """Response returned by the get jobs endpoint."""

    reference_number: str
    title: str
    company: str | None = None
    occupation: str | None = None


class JobLocationResponse(BaseModel):
    postal_code: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class JobDetailResponse(JobResponse):
    description: str | None = None
    offer_type: str | None = None
    full_time: bool | None = None
    contract_duration: str | None = None
    career_change_suitable: bool | None = None
    home_office_possible: bool | None = None
    temporary_employment: bool | None = None
    private_placement: bool | None = None
    salary_period: str | None = None
    salary_type: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    entry_date: str | None = None
    publication_date: str | None = None
    first_publication_date: str | None = None
    modified_at: str | None = None
    external_url: str | None = None
    partner_name: str | None = None
    partner_url: str | None = None
    employer_customer_hash: str | None = None
    locations: list[JobLocationResponse]


# endregion


# region Auxiliary functions


def _check_if_database_exists() -> None:
    """Check if the job database exists."""
    if not DATABASE_PATH.is_file():
        logger.error("Job database does not exist: %s", DATABASE_PATH)

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The job database is unavailable.",
        )


# endregion


# region API endpoints


@router.get(
    "",
    summary="Get jobs",
    response_description="A list of available jobs",
    response_model=list[JobResponse],
    responses={
        503: {
            "description": "The job database is unavailable",
        }
    },
)
def get_jobs(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of jobs to return",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of jobs to skip",
    ),
) -> list[JobResponse]:
    """
    Return jobs ordered by publication date, newest first.

    Use `limit` and `offset` to paginate through the available jobs.
    If the offset is beyond the available results, an empty list is returned.
    """
    _check_if_database_exists()

    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                GET_JOBS_SQL,
                (limit, offset),
            ).fetchall()

    except sqlite3.Error:
        logger.exception("Could not read the job database")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The job database is unavailable.",
        )

    return [JobResponse(**dict(row)) for row in rows]


@router.get(
    "/{reference_number}",
    summary="Get a single job",
    response_description="The complete job advertisement",
    response_model=JobDetailResponse,
    responses={
        404: {
            "description": "The requested job was not found",
        },
        503: {
            "description": "The job database is unavailable",
        },
    },
)
def get_single_job(reference_number: str) -> JobDetailResponse:
    """
    Return a complete job advertisement and all its locations.

    A 404 response is returned if the reference number is unknown.
    """
    _check_if_database_exists()

    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.row_factory = sqlite3.Row

            job_row = connection.execute(
                GET_SINGLE_JOB_SQL,
                (reference_number,),
            ).fetchone()

            if job_row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Job not found.",
                )

            location_rows = connection.execute(
                GET_JOB_LOCATIONS_SQL,
                (reference_number,),
            ).fetchall()

    except sqlite3.Error:
        logger.exception("Could not read the job database")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The job database is unavailable.",
        )

    job_data = dict(job_row)
    job_data["locations"] = [JobLocationResponse(**dict(row)) for row in location_rows]

    return JobDetailResponse(**job_data)


# endregion
