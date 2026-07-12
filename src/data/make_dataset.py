"""Download a small raw sample from the Arbeitsagentur job-search API."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    page_number = 1
    jobs_per_page = 10

    print(
        f"Searching for {keyword!r}, "  # !r uses repr() instead of str() for a developer-friendly representation
        f"page {page_number}, jobs per page {jobs_per_page}..."
    )

    search_result = arbeitsagentur_client.search_jobs(
        keyword=keyword,
        page_number=page_number,
        jobs_per_page=jobs_per_page,
    )

    extraction_time = datetime.now(timezone.utc)
    output_directory = RAW_DATA_DIRECTORY / extraction_time.strftime(
        "%Y-%m-%dT%H-%M-%SZ"
    )

    search_output_path = output_directory / "search-page-1.json"
    save_json(search_result, search_output_path)

    print(f"Raw search response saved to: {search_output_path}")

    jobs = search_result.get("ergebnisliste")
    if not isinstance(jobs, list):
        raise ValueError(
            "Expected search_result['ergebnisliste'] to be a list"
        )

    job_details: list[dict[str, Any]] = []

    for job_number, job in enumerate(jobs, start=1):
        if not isinstance(job, dict):
            raise ValueError("Expected every job to be a JSON object")

        reference_number = job.get("referenznummer")

        if not isinstance(reference_number, str) or not reference_number:
            print(
                f"Skipping job {job_number}: "
                "missing or invalid referenznummer"
            )
            continue

        print(
            f"Retrieving details for job {job_number}/{len(jobs)}: "
            f"{reference_number}"
        )

        details = arbeitsagentur_client.get_job_details(reference_number)
        job_details.append(details)

    details_output_path = output_directory / "job-details.json"
    save_json(job_details, details_output_path)

    print(f"Raw job details saved to: {details_output_path}")


if __name__ == "__main__":
    main()