from datetime import datetime
from pathlib import Path

from airflow.sdk import dag, task  # type: ignore

from src.config.settings import DEFAULT_JOB_SEARCH_KEYWORDS
from src.data.etl.extract_data import extract_data
from src.data.etl.transform_data import transform_data
from src.data.etl.load_data import load_data


@dag(
    schedule="0 6 * * *",
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=["job-market"],
)
def job_market_etl():

    @task
    def extract():
        return str(extract_data(DEFAULT_JOB_SEARCH_KEYWORDS))

    @task
    def transform(raw_path: str):
        return str(transform_data(Path(raw_path)))

    @task
    def load(clean_path: str):
        load_data(Path(clean_path))

    raw = extract()
    clean = transform(raw)
    load(clean)


job_market_etl()
