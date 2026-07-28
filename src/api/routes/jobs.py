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

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)

DATABASE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "processed" / "job_market.sqlite3"
)

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


class JobResponse(BaseModel):
    """Response returned by the get jobs endpoint."""

    reference_number: str
    title: str
    company: str | None = None
    occupation: str | None = None


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
    if not DATABASE_PATH.is_file():
        logger.error("Job database does not exist: %s", DATABASE_PATH)

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The job database is unavailable.",
        )

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
