"""
Application entry point for the Liora Job Market API.

Run from the project root with:
    python -m uvicorn src.api.main:api --reload

Swagger UI is available at:
    http://127.0.0.1:8000/docs
"""

from fastapi import FastAPI

from src.api.routes.jobs import router as jobs_router
from src.api.routes.health import router as health_router

api = FastAPI(
    title="Liora Job Market API",
    version="0.1.0",
)

api.include_router(health_router)
api.include_router(jobs_router)
