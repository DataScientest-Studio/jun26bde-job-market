#!/bin/sh
set -e

DB_PATH="/app/data/processed/job_market.sqlite3"

echo "Creating the dataset..."
python -m src.data.make_dataset

if [ ! -f "$DB_PATH" ]; then
    echo "Expected SQLite database not found: $DB_PATH"
    exit 1
fi

echo "SQLite database found: $DB_PATH"

echo "Starting FastAPI on port 8000..."
python -m uvicorn src.api.main:api \
    --host 0.0.0.0 \
    --port 8000 &

API_PID=$!

trap 'kill "$API_PID"' INT TERM EXIT

echo "Starting Dash on port 8050..."
python -c '
from src.dashboard.app import app
from src.config.settings import FRONTEND_PORT

app.run(
    host="0.0.0.0",
    port=FRONTEND_PORT,
    debug=False,
)
'