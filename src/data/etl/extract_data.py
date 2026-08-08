"""E/ETL: Extract raw job data from the Arbeitsagentur job-search API."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from src.config.settings import (
    FIRST_PAGE,
    JOB_DETAIL_FAILURES_FILE_NAME,
    JOB_DETAILS_FILE_NAME,
    JOBS_PER_PAGE,
    DEFAULT_JOB_SEARCH_KEYWORDS,
    NUMBER_OF_PAGES,
    RAW_DATA_DIRECTORY,
)
from src.data.arbeitsagentur_client import ArbeitsagenturClient
from src.data.utils.json_utils import save_json

logger = logging.getLogger(__name__)


def _search_jobs(
    client: ArbeitsagenturClient,
    *,
    keywords: tuple[str, ...],
    first_page: int,
    number_of_pages: int,
    jobs_per_page: int,
    output_directory: Path,
) -> list[dict[str, Any]]:
    job_summaries: list[dict[str, Any]] = []
    seen_reference_numbers: set[str] = set()

    for keyword in keywords:
        keyword_directory = (
            output_directory / "search-results" / keyword.lower().replace(" ", "-")
        )

        for page_number in range(
            first_page,
            first_page + number_of_pages,
        ):
            logger.info(
                "Searching for %r, page %d, jobs per page %d",
                keyword,
                page_number,
                jobs_per_page,
            )

            try:
                search_result = client.search_jobs(
                    keyword=keyword,
                    page_number=page_number,
                    jobs_per_page=jobs_per_page,
                )
            except requests.RequestException:
                logger.exception(
                    "Failed to retrieve page %d for %r",
                    page_number,
                    keyword,
                )
                continue

            save_json(
                search_result,
                keyword_directory / f"page-{page_number:03d}.json",
            )

            jobs = search_result.get("ergebnisliste")

            if not isinstance(jobs, list):
                logger.warning(
                    "Skipping page %d for %r: " "'ergebnisliste' is not a list",
                    page_number,
                    keyword,
                )
                continue

            for job in jobs:
                if not isinstance(job, dict):
                    logger.warning(
                        "Skipping malformed search-result entry: %r",
                        job,
                    )
                    continue

                reference_number = job.get("referenznummer")

                if not isinstance(reference_number, str) or not reference_number:
                    logger.warning(
                        "Skipping search result without a valid "
                        "reference number: %r",
                        job,
                    )
                    continue

                if reference_number in seen_reference_numbers:
                    continue

                seen_reference_numbers.add(reference_number)
                job_summaries.append(job)

    return job_summaries


def _retrieve_job_details(
    client: ArbeitsagenturClient,
    job_summaries: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    job_details: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for job_number, job_summary in enumerate(job_summaries, start=1):
        reference_number = job_summary["referenznummer"]

        logger.info(
            "Retrieving details for %d/%d: %s",
            job_number,
            len(job_summaries),
            reference_number,
        )

        try:
            details = client.get_job_details(reference_number)
        except requests.RequestException as error:
            logger.warning(
                "Failed to retrieve details for %s: %s",
                reference_number,
                error,
            )
            failures.append(
                {
                    "referenznummer": reference_number,
                    "error": str(error),
                }
            )
            continue

        job_details.append(details)

    return job_details, failures


def extract_data(keywords: tuple[str, ...]) -> Path:
    """Extract raw job data and return the path to the job-details.json file."""
    extraction_time = datetime.now(timezone.utc)
    output_directory = RAW_DATA_DIRECTORY / extraction_time.strftime(
        "%Y-%m-%dT%H-%M-%SZ"
    )
    details_output_path = output_directory / JOB_DETAILS_FILE_NAME
    failures_output_path = output_directory / JOB_DETAIL_FAILURES_FILE_NAME

    client = ArbeitsagenturClient()

    job_summaries = _search_jobs(
        client,
        keywords=keywords,
        first_page=FIRST_PAGE,
        number_of_pages=NUMBER_OF_PAGES,
        jobs_per_page=JOBS_PER_PAGE,
        output_directory=output_directory,
    )

    logger.info(
        "Retrieved %d unique search results",
        len(job_summaries),
    )

    job_details, failed_jobs = _retrieve_job_details(
        client,
        job_summaries,
    )

    save_json(job_details, details_output_path)
    save_json(failed_jobs, failures_output_path)

    logger.info(
        "Extraction finished: %d details retrieved, %d detail requests failed",
        len(job_details),
        len(failed_jobs),
    )
    logger.info("Raw job details saved to %s", details_output_path)

    return details_output_path


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    extract_data(DEFAULT_JOB_SEARCH_KEYWORDS)


if __name__ == "__main__":
    main()
