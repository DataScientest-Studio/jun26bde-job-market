"""Shared access to the processed SQLite job database."""

from collections.abc import Generator
from contextlib import contextmanager
import sqlite3

from src.config.settings import DATABASE_PATH


class DatabaseUnavailableError(Exception):
    """Raised when the job database cannot be accessed."""


@contextmanager
def get_database_connection() -> Generator[sqlite3.Connection, None, None]:
    """Provide a configured connection to the job database."""
    if not DATABASE_PATH.is_file():
        raise DatabaseUnavailableError(f"Job database does not exist: {DATABASE_PATH}")

    connection = None

    try:
        connection = sqlite3.connect(DATABASE_PATH)
        connection.row_factory = sqlite3.Row
        yield connection
    except sqlite3.Error as error:
        raise DatabaseUnavailableError("Could not access the job database.") from error
    finally:
        if connection is not None:
            connection.close()
