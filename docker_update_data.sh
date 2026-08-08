#!/bin/sh

docker compose build app

docker compose run --rm app \
    python -m src.data.etl.etl "$@"
	
# Example: ./docker_update_data.sh --keyword "Data Engineer" --keyword "AI Engineer"