"""
API routes for reading job advertisements from the processed SQLite database.

The endpoints in this module provide read-only access to jobs previously
collected and processed by the data pipeline.
"""

import logging
from pathlib import Path
import sqlite3

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

# region Setup

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/statistics",
    tags=["Statistics"],
)

# endregion


# region Constants

DATABASE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "processed" / "job_market.sqlite3"
)

# endregion


# region SQL queries

GET_OVERVIEW_SQL = """
SELECT
    COUNT(*) AS total_jobs,
    COUNT(
        DISTINCT CASE
            WHEN TRIM(company) <> '' THEN company
        END
    ) AS total_companies,
    MIN(publication_date) AS earliest_publication_date,
    MAX(publication_date) AS latest_publication_date
FROM jobs
"""

GET_TOTAL_LOCATIONS_SQL = """
SELECT COUNT(*) AS total_locations
FROM (
    SELECT DISTINCT
        city,
        region,
        country
    FROM job_locations
    WHERE city IS NOT NULL
      AND TRIM(city) <> ''
)
"""

GET_COMPANY_STATISTICS_SQL = """
SELECT
    company,
    COUNT(*) AS job_count
FROM jobs
WHERE company IS NOT NULL
  AND TRIM(company) <> ''
GROUP BY company
ORDER BY job_count DESC, company ASC
LIMIT ?
"""

GET_LOCATION_STATISTICS_SQL = """
SELECT
    city,
    region,
    country,
    COUNT(DISTINCT reference_number) AS job_count
FROM job_locations
WHERE city IS NOT NULL
  AND TRIM(city) <> ''
GROUP BY
    city,
    region,
    country
ORDER BY
    job_count DESC,
    country ASC,
    region ASC,
    city ASC
LIMIT ?
"""


GET_HOME_OFFICE_STATISTICS_SQL = """
SELECT
    COUNT(
        CASE WHEN home_office_possible = 1 THEN 1 END
    ) AS possible,
    COUNT(
        CASE WHEN home_office_possible = 0 THEN 1 END
    ) AS not_possible,
    COUNT(
        CASE WHEN home_office_possible IS NULL THEN 1 END
    ) AS unknown
FROM jobs
"""

# endregion


# region Pydantic models


class StatisticsOverviewModel(BaseModel):
    """An overview of the job advertisements stored in the database."""

    total_jobs: int
    total_companies: int
    total_locations: int
    earliest_publication_date: str | None = None
    latest_publication_date: str | None = None


class CompanyStatisticsModel(BaseModel):
    """The number of job advertisements stored for a company."""

    company: str
    job_count: int


class LocationStatisticsModel(BaseModel):
    """The number of job advertisements stored for a location."""

    city: str
    region: str | None = None
    country: str | None = None
    job_count: int


class HomeOfficeStatisticsModel(BaseModel):
    """The availability of home office among stored job advertisements."""

    possible: int
    not_possible: int
    unknown: int


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
    "/overview",
    summary="Get job statistics overview",
    response_description="An overview of the stored job advertisements",
    response_model=StatisticsOverviewModel,
    responses={
        503: {
            "description": "The job database is unavailable",
        }
    },
)
def get_overview() -> StatisticsOverviewModel:
    """
    Return general statistics about the stored job advertisements.
    """
    _check_if_database_exists()

    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.row_factory = sqlite3.Row
            overview_row = connection.execute(GET_OVERVIEW_SQL).fetchone()
            locations_row = connection.execute(GET_TOTAL_LOCATIONS_SQL).fetchone()
    except sqlite3.Error:
        logger.exception("Could not read statistics from the job database")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The job database is unavailable.",
        )

    overview_data = dict(overview_row)
    overview_data["total_locations"] = locations_row["total_locations"]

    return StatisticsOverviewModel(**overview_data)


@router.get(
    "/companies",
    summary="Get company statistics",
    response_description="Companies and their numbers of job advertisements",
    response_model=list[CompanyStatisticsModel],
    responses={
        503: {
            "description": "The job database is unavailable",
        }
    },
)
def get_company_statistics(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of companies to return",
        examples=[5, 10, 20],
        openapi_examples={
            "small": {
                "summary": "Five companies",
                "value": 5,
            },
            "medium": {
                "summary": "Ten companies",
                "value": 10,
            },
            "large": {
                "summary": "Twenty companies",
                "value": 20,
            },
        },
    ),
) -> list[CompanyStatisticsModel]:
    """
    Return companies ordered by their number of job advertisements.

    Companies without a name are excluded.
    """
    _check_if_database_exists()

    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                GET_COMPANY_STATISTICS_SQL,
                (limit,),
            ).fetchall()

    except sqlite3.Error:
        logger.exception("Could not read company statistics from the job database")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The job database is unavailable.",
        )

    return [CompanyStatisticsModel(**dict(row)) for row in rows]


@router.get(
    "/locations",
    summary="Get location statistics",
    response_description="Locations and their numbers of job advertisements",
    response_model=list[LocationStatisticsModel],
    responses={
        503: {
            "description": "The job database is unavailable",
        }
    },
)
def get_location_statistics(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of locations to return",
        examples=[5, 10, 20],
        openapi_examples={
            "small": {
                "summary": "Five locations",
                "value": 5,
            },
            "medium": {
                "summary": "Ten locations",
                "value": 10,
            },
            "large": {
                "summary": "Twenty locations",
                "value": 20,
            },
        },
    ),
) -> list[LocationStatisticsModel]:
    """
    Return locations ordered by their number of job advertisements.

    Locations without a city are excluded.
    """
    _check_if_database_exists()

    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.row_factory = sqlite3.Row

            rows = connection.execute(
                GET_LOCATION_STATISTICS_SQL,
                (limit,),
            ).fetchall()

    except sqlite3.Error:
        logger.exception("Could not read location statistics from the job database")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The job database is unavailable.",
        )

    return [LocationStatisticsModel(**dict(row)) for row in rows]


@router.get(
    "/home-office",
    summary="Get home-office statistics",
    response_description=(
        "Numbers of jobs with possible, unavailable, or unknown home office"
    ),
    response_model=HomeOfficeStatisticsModel,
    responses={
        503: {
            "description": "The job database is unavailable",
        }
    },
)
def get_home_office_statistics() -> HomeOfficeStatisticsModel:
    """
    Return job counts grouped by home-office availability.
    """
    _check_if_database_exists()

    try:
        with sqlite3.connect(DATABASE_PATH) as connection:
            connection.row_factory = sqlite3.Row

            row = connection.execute(GET_HOME_OFFICE_STATISTICS_SQL).fetchone()

    except sqlite3.Error:
        logger.exception("Could not read home-office statistics from the job database")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The job database is unavailable.",
        )

    return HomeOfficeStatisticsModel(**dict(row))


# endregion
