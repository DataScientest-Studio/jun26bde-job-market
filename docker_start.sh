#!/bin/sh

set -e

SWAGGER_URL="http://127.0.0.1:8000/docs"
HEALTH_URL="http://127.0.0.1:8000/health"
DASH_URL="http://127.0.0.1:8050"

docker compose up -d

wait_for_url() {
    url="$1"
    service_name="$2"
    maximum_attempts=60
    attempt=1

    while [ "$attempt" -le "$maximum_attempts" ]; do
        if curl -fs "$url" >/dev/null 2>&1; then
            return 0
        fi

        container_id=$(docker compose ps -q "$service_name")

        if [ -z "$container_id" ] ||
           [ "$(docker inspect -f '{{.State.Running}}' "$container_id" 2>/dev/null)" != "true" ]; then
            echo "ERROR: Docker service '$service_name' stopped before becoming ready." >&2
            echo >&2
            docker compose logs "$service_name" >&2
            exit 1
        fi

        sleep 1
        attempt=$((attempt + 1))
    done

    echo "ERROR: Timed out waiting for $url" >&2
    docker compose logs "$service_name" >&2
    exit 1
}

echo "Waiting for FastAPI..."
wait_for_url "$HEALTH_URL" app

echo "Waiting for Dash..."
wait_for_url "$DASH_URL" app

python -c '
import sys
import webbrowser

for url in sys.argv[1:]:
    webbrowser.open(url)
' "$SWAGGER_URL" "$DASH_URL"

echo "Swagger is ready at $SWAGGER_URL"
echo "Dash    is ready at $DASH_URL"