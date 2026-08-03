"""API route for displaying job locations on an interactive map."""

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import HTMLResponse

from src.data.sqlite_database import DatabaseUnavailableError
from src.visualization.job_map import build_job_map_html

router = APIRouter(
    prefix="/map",
    tags=["Map"],
)


@router.get(
    "",
    response_class=HTMLResponse,
    summary="Display job map",
    response_description="An interactive HTML map of job locations",
    responses={
        404: {"description": "No job locations with coordinates were found"},
        503: {"description": "The job database is unavailable"},
    },
)
def get_map(
    search: str | None = Query(
        default=None,
        description="Search in job title, occupation, company, and description",
    ),
) -> HTMLResponse:
    try:
        return HTMLResponse(content=build_job_map_html(search=search))
    except DatabaseUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
