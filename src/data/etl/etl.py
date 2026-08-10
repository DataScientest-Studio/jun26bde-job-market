import argparse

from src.config.settings import DEFAULT_JOB_SEARCH_KEYWORDS
from src.data.etl.extract_data import extract_data
from src.data.etl.transform_data import transform_data
from src.data.etl.load_data import load_data


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


def main() -> None:
    arguments = _parse_arguments()

    keywords = (
        tuple(arguments.keywords)
        if arguments.keywords
        else DEFAULT_JOB_SEARCH_KEYWORDS
    )

    raw_path = extract_data(keywords)
    clean_path = transform_data(raw_path)
    load_data(clean_path)


if __name__ == "__main__":
    main()