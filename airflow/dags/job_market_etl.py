from datetime import datetime
from pathlib import Path

from airflow.sdk import dag, task  # type: ignore

from src.config.settings import DEFAULT_JOB_SEARCH_KEYWORDS
from src.data.etl.extract_data import extract_data
from src.data.etl.transform_data import transform_data
from src.data.etl.load_data import load_data
from src.data.job_freshness import update_job_freshness


@dag(
    schedule="0 6 * * *",
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["job-market"],
)
def job_market_etl():

    @task(multiple_outputs=True)
    def extract():
        raw_path, seen_reference_numbers = extract_data(DEFAULT_JOB_SEARCH_KEYWORDS)

        return {
            "raw_path": str(raw_path),
            "seen_reference_numbers": list(seen_reference_numbers),
        }

    @task
    def transform(raw_path: str):
        return str(transform_data(Path(raw_path)))

    @task
    def load(clean_path: str) -> str:
        load_data(Path(clean_path))
        return clean_path

    @task
    def update_freshness(
        seen_reference_numbers: list[str],
        _: str,
    ) -> None:
        update_job_freshness(set(seen_reference_numbers))

    extracted_data = extract()
    clean_data = transform(extracted_data["raw_path"])
    loaded_data_path = load(clean_data)

    update_freshness(
        extracted_data["seen_reference_numbers"],
        loaded_data_path,
    )

    # extract → transform → load → update job freshness


job_market_etl()
