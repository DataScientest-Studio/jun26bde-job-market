"""Download a small raw sample from the Arbeitsagentur job-search API."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from src.config.settings import (
    DATABASE_PATH,
    FIRST_PAGE,
    JOBS_PER_PAGE,
    KEYWORDS,
    NUMBER_OF_PAGES,
    RAW_DATA_DIRECTORY,
)
from src.data.arbeitsagentur_client import ArbeitsagenturClient
from src.data.sqlite_loader import (
    load_clean_jobs_to_sqlite,
)
from src.data.job_location_geocoder import JobLocationGeocoder

logger = logging.getLogger(__name__)


def _save_json(data: Any, target_path: Path) -> None:
    """Write JSON-compatible data as UTF-8 JSON."""

    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def _clean_job(raw_job: dict[str, Any]) -> dict[str, Any]:
    """Convert one raw Arbeitsagentur job into our cleaner structure."""

    raw_locations = raw_job.get("stellenlokationen", [])
    clean_locations: list[dict[str, Any]] = []

    if not isinstance(raw_locations, list):
        logger.warning(
            "Ignoring malformed 'stellenlokationen' value: %r",
            raw_locations,
        )
        raw_locations = []

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

            _save_json(
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


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    extraction_time = datetime.now(timezone.utc)
    output_directory = RAW_DATA_DIRECTORY / extraction_time.strftime(
        "%Y-%m-%dT%H-%M-%SZ"
    )

    client = ArbeitsagenturClient()

    job_summaries = _search_jobs(
        client,
        keywords=KEYWORDS,
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

    details_output_path = output_directory / "job-details.json"
    failures_output_path = output_directory / "job-detail-failures.json"

    _save_json(job_details, details_output_path)
    _save_json(failed_jobs, failures_output_path)

    clean_jobs = [_clean_job(job) for job in job_details]

    geocoder = JobLocationGeocoder()
    clean_jobs, num_malformed_locations = geocoder.enrich_jobs_with_geocoding(
        clean_jobs
    )

    clean_output_path = output_directory / "clean-jobs.json"
    _save_json(clean_jobs, clean_output_path)

    num_loaded_jobs, num_skipped_jobs = load_clean_jobs_to_sqlite(
        jobs=clean_jobs,
    )

    logger.info(
        "Pipeline finished: %d details retrieved, "
        "%d detail requests failed, %d jobs loaded, "
        "%d jobs skipped, %d malformed locations skipped",
        len(job_details),
        len(failed_jobs),
        num_loaded_jobs,
        num_skipped_jobs,
        num_malformed_locations,
    )
    logger.info("Raw job details saved to %s", details_output_path)
    logger.info("Clean job data saved to %s", clean_output_path)
    logger.info("SQLite database updated: %s", DATABASE_PATH)


if __name__ == "__main__":
    main()
