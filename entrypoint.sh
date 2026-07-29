#!/bin/sh
set -e

DB_PATH="/app/src/data/processed/job_market.sqlite3"

flake8 --exclude=.venv,venv .

python -m src.data.make_dataset

if [ -f "$DB_PATH" ]; then
  echo "SQLite file found: $DB_PATH"
else
  echo "Expected SQLite file not found: $DB_PATH"
  exit 1
fi

echo "checked database. Mapping..."

python -m src.features.docker_mapping

echo "map done"
