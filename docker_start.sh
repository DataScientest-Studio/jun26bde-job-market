#!/bin/sh

set -e

SWAGGER_URL="http://127.0.0.1:8000/docs"
DASH_URL="http://127.0.0.1:8050"

docker compose up -d

echo "Waiting for FastAPI..."

until curl -fs http://127.0.0.1:8000/health >/dev/null 2>&1; do
    sleep 1
done

echo "Waiting for Dash..."

until curl -fs "$DASH_URL" >/dev/null 2>&1; do
    sleep 1
done

if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$SWAGGER_URL" >/dev/null 2>&1 &
    xdg-open "$DASH_URL" >/dev/null 2>&1 &
else
    echo "xdg-open is not available."
fi

echo "Swagger is ready at $SWAGGER_URL"
echo "Dash    is ready at $DASH_URL"