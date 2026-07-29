"""
API routes for reading job advertisements from the processed SQLite database.

The endpoints in this module provide read-only access to jobs previously
collected and processed by the data pipeline.
"""

import logging

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.data.sqlite_database import (
    DatabaseUnavailableError,
    get_database_connection,
)

# region Setup

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)

# endregion


# region SQL queries

# Retrieve summary information for all stored jobs.
GET_ALL_JOBS_SQL = """
SELECT
    reference_number,
    title,
    company,
    occupation
FROM jobs
"""

# Retrieve all available details for one job.
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

# Retrieve all locations associated with one job.
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


# region Pydantic models


class JobModel(BaseModel):
    """A compact representation of a job advertisement."""

    reference_number: str
    title: str
    company: str | None = None
    occupation: str | None = None


class JobLocationModel(BaseModel):
    """A geographical location associated with a job advertisement."""

    postal_code: str | None = None
    city: str | None = None
    region: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class JobDetailModel(JobModel):
    """A complete job advertisement, including details and locations."""

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
    # ensures that the default value is a new empty list for EACH instance:
    locations: list[JobLocationModel] = Field(default_factory=list)


# endregion


# region API endpoints


@router.get(
    "",
    summary="Get jobs",
    response_description="A list of available jobs",
    response_model=list[JobModel],
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
        examples=[5, 10, 20],
        openapi_examples={
            "small": {
                "summary": "Small result set",
                "value": 5,
            },
            "medium": {
                "summary": "Medium result set",
                "value": 10,
            },
            "large": {
                "summary": "Large result set",
                "value": 20,
            },
        },
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of jobs to skip",
        examples=[0],
    ),
    city: str | None = Query(
        default=None,
        description="City to filter jobs by",
        examples=["Berlin", "München", "Hamburg"],
    ),
    company: str | None = Query(
        default=None,
        description="Company name to filter jobs by",
        examples=["FERCHAU"],
        openapi_examples={
            "FERCHAU": {
                "summary": "FERCHAU GmbH",
                "value": "FERCHAU",
            },
        },
    ),
    home_office: bool | None = Query(
        default=None,
        description="Filter by home-office availability",
        examples=[None, True, False],
    ),
) -> list[JobModel]:
    """
    Return jobs ordered by publication date, newest first.

    Use `limit` and `offset` to paginate through the available jobs.
    If the offset is beyond the available results, an empty list is returned.

    Optional query parameters can be used to filter the results by
    - city,
    - company name
    - home-office availability.
    """

    query_conditions = []
    query_parameters = []

    if city is not None:
        query_conditions.append("""
            EXISTS (
                SELECT 1
                FROM job_locations
                WHERE job_locations.reference_number = jobs.reference_number
                  AND LOWER(job_locations.city) = LOWER(?)
            )
            """)
        query_parameters.append(city)

    if company is not None:
        query_conditions.append("LOWER(company) LIKE LOWER(?)")
        query_parameters.append(f"%{company}%")

    if home_office is not None:
        query_conditions.append("home_office_possible = ?")
        query_parameters.append(home_office)

    query = GET_ALL_JOBS_SQL

    if query_conditions:
        query += " WHERE " + " AND ".join(query_conditions)

    query += """
    ORDER BY publication_date DESC, reference_number ASC
    LIMIT ? OFFSET ?
    """

    query_parameters.extend([limit, offset])

    try:
        with get_database_connection() as connection:
            rows = connection.execute(query, query_parameters).fetchall()
    except DatabaseUnavailableError:
        logger.exception("Could not read the job database")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The job database is unavailable.",
        )

    return [JobModel(**dict(row)) for row in rows]


@router.get(
    "/{reference_number}",
    summary="Get a single job",
    response_description="The complete job advertisement",
    response_model=JobDetailModel,
    responses={
        404: {
            "description": "The requested job was not found",
        },
        503: {
            "description": "The job database is unavailable",
        },
    },
)
def get_single_job(reference_number: str) -> JobDetailModel:
    """
    Return a complete job advertisement and all its locations.

    A 404 response is returned if the reference number is unknown.
    """
    try:
        with get_database_connection() as connection:

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

    except DatabaseUnavailableError:
        logger.exception("Could not read the job database")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The job database is unavailable.",
        )

    job_data = dict(job_row)
    job_data["locations"] = [JobLocationModel(**dict(row)) for row in location_rows]

    return JobDetailModel(**job_data)


# endregion
