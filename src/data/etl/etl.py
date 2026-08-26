import argparse
import time

from src.config.settings import DEFAULT_JOB_SEARCH_KEYWORDS, PUSHGATEWAY_URL
from src.data.etl.extract_data import extract_data
from src.data.etl.transform_data import transform_data
from src.data.etl.load_data import load_data
from src.data.job_freshness import update_job_freshness
from src.monitoring.metrics import monitor_etl_run


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the complete job-market ETL pipeline."
    )

    parser.add_argument(
        "--keyword",
        action="append",
        dest="keywords",
        help="Job-search keyword. Can be specified multiple times.",
    )

    return parser.parse_args()


@monitor_etl_run
def main() -> None:
    arguments = _parse_arguments()

    keywords = (
        tuple(arguments.keywords) if arguments.keywords else DEFAULT_JOB_SEARCH_KEYWORDS
    )

    raw_path, seen_reference_numbers = extract_data(keywords)
    clean_path = transform_data(raw_path)
    load_data(clean_path)
    update_job_freshness(seen_reference_numbers)


if __name__ == "__main__":
    main()
