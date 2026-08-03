"""
Application entry point for the Liora Job Market API.

Run from the project root with:
    python -m uvicorn src.api.main:api --reload

Run in Docker with:
    exec python -m uvicorn src.api.main:api --host 0.0.0.0 --port 8000

Swagger UI is available at:
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI

from src.api.routes.jobs import router as jobs_router
from src.api.routes.health import router as health_router
from src.api.routes.statistics import router as statistics_router
from src.api.routes.map import router as map_router

api = FastAPI(
    title="Liora Job Market API",
    version="0.1.0",
)

api.include_router(health_router)
api.include_router(jobs_router)
api.include_router(statistics_router)
api.include_router(map_router)
