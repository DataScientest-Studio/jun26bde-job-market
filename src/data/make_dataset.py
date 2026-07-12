"""Download a small raw sample from the Arbeitsagentur job-search API."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import requests

from src.data.arbeitsagentur_client import ArbeitsagenturClient

RAW_DATA_DIRECTORY = Path(__file__).resolve().parent / "raw" / "arbeitsagentur"


def save_json(data: Any, target_path: Path) -> None:
    """Write JSON-compatible data as UTF-8 JSON."""

    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:
    arbeitsagentur_client = ArbeitsagenturClient()

    keyword = "Data Engineer"
    first_page = 1
    number_of_pages = 3
    jobs_per_page = 10

    extraction_time = datetime.now(timezone.utc)
    output_directory = RAW_DATA_DIRECTORY / extraction_time.strftime(
        "%Y-%m-%dT%H-%M-%SZ"
    )

    all_jobs: list[dict[str, Any]] = []

    for page_number in range(
        first_page,
        first_page + number_of_pages,
    ):
        print(
            f"Searching for {keyword!r}, "
            f"page {page_number}, "
            f"jobs per page {jobs_per_page}..."
        )

        try:
            search_result = arbeitsagentur_client.search_jobs(
                keyword=keyword,
                page_number=page_number,
                jobs_per_page=jobs_per_page,
            )
        except requests.RequestException as error:
            print(f"Failed to retrieve search page " f"{page_number}: {error}")
            continue

        search_output_path = output_directory / f"search-page-{page_number}.json"
        save_json(search_result, search_output_path)

        print(f"Raw search response saved to: {search_output_path}")

        jobs = search_result.get("ergebnisliste")

        if not isinstance(jobs, list):
            print(f"Skipping page {page_number}: " "'ergebnisliste' is not a list")
            continue

        all_jobs.extend(jobs)

    print(f"Retrieved {len(all_jobs)} search results in total.")

    job_details: list[dict[str, Any]] = []
    failed_jobs: list[dict[str, str]] = []

    for job_number, job in enumerate(all_jobs, start=1):
        reference_number = job.get("referenznummer")

        if not isinstance(reference_number, str) or not reference_number:
            print(f"Skipping job {job_number}: " "missing or invalid referenznummer")
            continue

        print(
            f"Retrieving details for "
            f"{job_number}/{len(all_jobs)}: "
            f"{reference_number}"
        )

        try:
            details = arbeitsagentur_client.get_job_details(reference_number)
        except requests.RequestException as error:
            print(f"Failed to retrieve {reference_number}: " f"{error}")

            failed_jobs.append(
                {
                    "referenznummer": reference_number,
                    "error": str(error),
                }
            )
            continue

        job_details.append(details)

    details_output_path = output_directory / "job-details.json"
    save_json(job_details, details_output_path)

    failures_output_path = output_directory / "job-detail-failures.json"
    save_json(failed_jobs, failures_output_path)

    print(f"Successfully retrieved " f"{len(job_details)}/{len(all_jobs)} job details.")
    print(f"Raw job details saved to: {details_output_path}")

    if failed_jobs:
        print(
            f"{len(failed_jobs)} detail requests failed. "
            f"Failures saved to: {failures_output_path}"
        )


if __name__ == "__main__":
    main()
