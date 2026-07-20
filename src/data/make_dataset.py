"""Download a small raw sample from the Arbeitsagentur job-search API."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import requests

from src.data.arbeitsagentur_client import ArbeitsagenturClient

from src.data.sqlite_loader import (
    DEFAULT_DATABASE_PATH,
    load_clean_jobs_to_sqlite,
)

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


def clean_job(raw_job: dict[str, Any]) -> dict[str, Any]:
    """Convert one raw Arbeitsagentur job into our cleaner structure."""

    raw_locations = raw_job.get("stellenlokationen", [])
    clean_locations: list[dict[str, Any]] = []

    if isinstance(raw_locations, list):
        for raw_location in raw_locations:
            if not isinstance(raw_location, dict):
                continue

            raw_address = raw_location.get("adresse", {})

            if not isinstance(raw_address, dict):
                raw_address = {}

            clean_locations.append(
                {
                    "postal_code": raw_address.get("plz"),
                    "city": raw_address.get("ort"),
                    "region": raw_address.get("region"),
                    "country": raw_address.get("land"),
                    "latitude": raw_location.get("breite"),
                    "longitude": raw_location.get("laenge"),
                }
            )

    entry_period = raw_job.get("eintrittszeitraum", {})
    publication_period = raw_job.get("veroeffentlichungszeitraum", {})

    if not isinstance(entry_period, dict):
        entry_period = {}

    if not isinstance(publication_period, dict):
        publication_period = {}

    return {
        "reference_number": raw_job.get("referenznummer"),
        "title": raw_job.get("stellenangebotsTitel"),
        "occupation": raw_job.get("hauptberuf"),
        "company": raw_job.get("firma"),
        "description": raw_job.get("stellenangebotsBeschreibung"),
        "offer_type": raw_job.get("stellenangebotsart"),
        "full_time": raw_job.get("arbeitszeitVollzeit"),
        "contract_duration": raw_job.get("vertragsdauer"),
        "career_change_suitable": raw_job.get("quereinstiegGeeignet"),
        "home_office_possible": raw_job.get("homeofficemoeglich"),
        "temporary_employment": raw_job.get("istArbeitnehmerUeberlassung"),
        "private_placement": raw_job.get("istPrivateArbeitsvermittlung"),
        "salary_period": raw_job.get("verguetungsangabe"),
        "salary_type": raw_job.get("artDerVerguetung"),
        "salary_min": raw_job.get("gehaltsspanneVon"),
        "salary_max": raw_job.get("gehaltsspanneBis"),
        "entry_date": entry_period.get("von"),
        "publication_date": publication_period.get("von"),
        "first_publication_date": raw_job.get("datumErsteVeroeffentlichung"),
        "modified_at": raw_job.get("aenderungsdatum"),
        "external_url": raw_job.get("externeURL"),
        "partner_name": raw_job.get("allianzpartnerName"),
        "partner_url": raw_job.get("allianzpartnerUrl"),
        "employer_customer_hash": raw_job.get("arbeitgeberKundennummerHash"),
        "locations": clean_locations,
    }


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

    clean_jobs = [clean_job(raw_job) for raw_job in job_details]

    clean_output_path = output_directory / "clean-jobs.json"
    save_json(clean_jobs, clean_output_path)

    num_loaded_jobs, num_skipped_jobs = load_clean_jobs_to_sqlite(
        jobs=clean_jobs,
    )

    print(f"Successfully retrieved {len(job_details)}/{len(all_jobs)} job details.")
    print(f"Raw job details saved to: {details_output_path}")
    print(f"Clean job data saved to: {clean_output_path}")
    print(f"SQLite database updated: {DEFAULT_DATABASE_PATH}")
    print(f"# Jobs loaded into SQLite: {num_loaded_jobs}")
    print(f"# Jobs skipped during database loading: {num_skipped_jobs}")

    if failed_jobs:
        print(
            f"{len(failed_jobs)} detail requests failed. "
            f"Failures saved to: {failures_output_path}"
        )


if __name__ == "__main__":
    main()
