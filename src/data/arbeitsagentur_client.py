"""HTTP client for the Arbeitsagentur job-search interface."""

from __future__ import annotations

import base64
from typing import Any

import requests


class ArbeitsagenturClient:
    """Small client for searching Arbeitsagentur job advertisements."""

    BASE_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service"
    JOBS_URL = f"{BASE_URL}/pc/v6/jobs"
    JOB_DETAILS_URL = f"{BASE_URL}/pc/v4/jobdetails"

    API_KEY = "jobboerse-jobsuche"

    KEYWORD_SEARCH_PARAM = "was"
    LOCATION_SEARCH_PARAM = "wo"
    PAGE_SEARCH_PARAM = "page"
    JOBS_PER_PAGE_SEARCH_PARAM = "size"

    def __init__(self, timeout_seconds: int = 30) -> None:
        self.timeout_seconds = timeout_seconds

        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-API-Key": self.API_KEY,
                "Accept": "application/json",
                "User-Agent": "jun26bde-job-market/0.1",
            }
        )

    def search_jobs(
        self,
        keyword: str,
        *,  # location, page_number and jobs_per_page are keyword-only arguments (must be specified with their names on the call)
        location: str | None = None,
        page_number: int = 1,
        jobs_per_page: int = 25,
    ) -> dict[str, Any]:
        """Search for job advertisements."""

        if page_number < 1:
            raise ValueError("page_number must be at least 1")

        if not 1 <= jobs_per_page <= 100:
            raise ValueError("jobs_per_page must be between 1 and 100")

        params: dict[str, str | int] = {
            self.KEYWORD_SEARCH_PARAM: keyword,
            self.PAGE_SEARCH_PARAM: page_number,
            self.JOBS_PER_PAGE_SEARCH_PARAM: jobs_per_page,
        }

        if location:
            params[self.LOCATION_SEARCH_PARAM] = location

        response = self.session.get(
            self.JOBS_URL,
            params=params,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise ValueError("Expected the API response to be a JSON object")

        return data

    def get_job_details(self, reference_number: str) -> dict[str, Any]:
        """Retrieve the full details for one job advertisement."""

        if not reference_number:
            raise ValueError("reference_number must not be empty")

        encoded_reference_number = base64.b64encode(
            reference_number.encode("utf-8")
        ).decode("ascii")

        response = self.session.get(
            f"{self.JOB_DETAILS_URL}/{encoded_reference_number}",
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise ValueError("Expected the API response to be a JSON object")

        return data