#!/bin/sh

set -e

docker compose run --rm --build data-update python -m src.data.etl.etl "$@"
	
# Example: ./docker_update_data.sh --keyword "Data Engineer" --keyword "AI Engineer"