"""Small mock of the Arbeitsagentur job-search API for local development."""

import base64
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

api = FastAPI(title="Mock Job API")


JOBS: list[dict[str, Any]] = [
    {
        "referenznummer": "MOCK-001",
        "titel": "Data Engineer",
        "arbeitgeber": "Example GmbH",
        "beruf": "Data Engineer",
        "aenderungsdatum": "2026-08-23T10:00:00",
    },
    {
        "referenznummer": "MOCK-002",
        "titel": "Senior Data Analyst",
        "arbeitgeber": "Analytics GmbH",
        "beruf": "Data-Analyst/in",
        "aenderungsdatum": "2026-08-22T10:00:00",
    },
    {
        "referenznummer": "MOCK-003",
        "titel": "Machine Learning Engineer",
        "arbeitgeber": "AI Systems GmbH",
        "beruf": "Informatiker/in",
        "aenderungsdatum": "2026-08-21T10:00:00",
    },
]


@api.get("/jobboerse/jobsuche-service/pc/v6/jobs")
def search_jobs(
    was: str = "",
    page: int = 1,
    size: int = 25,
) -> dict[str, Any]:
    matching_jobs = [job for job in JOBS if was.lower() in job["titel"].lower()]

    start = (page - 1) * size
    end = start + size

    return {
        "maxErgebnisse": len(matching_jobs),
        "page": page,
        "size": size,
        "ergebnisliste": matching_jobs[start:end],
    }


@api.get("/jobboerse/jobsuche-service/pc/v4/jobdetails/{encoded_reference}")
def get_job_details(encoded_reference: str) -> Any:
    try:
        reference_number = base64.b64decode(encoded_reference).decode("utf-8")
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid reference number.",
        ) from error

    for job in JOBS:
        if job["referenznummer"] == reference_number:
            return {
                "referenznummer": job["referenznummer"],
                "stellenangebotsTitel": job["titel"],
                "hauptberuf": job["beruf"],
                "firma": job["arbeitgeber"],
                "stellenangebotsBeschreibung": (
                    f"Mock description for {job['titel']}."
                ),
                "stellenangebotsart": "ARBEIT",
                "arbeitszeitVollzeit": True,
                "vertragsdauer": "UNBEFRISTET",
                "quereinstiegGeeignet": False,
                "stellenlokationen": [
                    {
                        "adresse": {
                            "plz": "49074",
                            "ort": "Osnabrück",
                            "region": "Niedersachsen",
                            "land": "Deutschland",
                        },
                        "breite": 52.2799,
                        "laenge": 8.0472,
                    }
                ],
                "datumErsteVeroeffentlichung": "2026-08-01",
                "aenderungsdatum": job["aenderungsdatum"],
                "veroeffentlichungszeitraum": {
                    "von": "2026-08-01",
                    "bis": "2026-09-30",
                },
            }

    return JSONResponse(
        status_code=404,
        content={
            "messages": [
                {
                    "code": "STELLENANGEBOT_NICHT_GEFUNDEN",
                }
            ]
        },
    )
