from __future__ import annotations

import time
from typing import Any

from geopy.exc import GeopyError
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim


class JobLocationGeocoder:
    def __init__(
        self,
        user_agent: str = "job-market-mapper",
        delay_seconds: float = 1.0,
        max_retries: int = 2,
        error_wait_seconds: float = 5.0,
    ) -> None:
        self.geolocator = Nominatim(user_agent=user_agent)
        self.delay_seconds = delay_seconds
        self._geocode = RateLimiter(
            self.geolocator.geocode,
            min_delay_seconds=delay_seconds,
            max_retries=max_retries,
            error_wait_seconds=error_wait_seconds,
            swallow_exceptions=True,
            return_value_on_exception=None,
        )
        self._cache: dict[str, tuple[float | None, float | None]] = {}

    @staticmethod
    def _clean_part(value: Any) -> str | None:
        if value is None:
            return None
        cleaned = str(value).strip()
        return cleaned or None

    def geocode_location(
        self,
        postal_code: Any = None,
        city: Any = None,
        country: Any = None,
    ) -> tuple[float | None, float | None]:
        postal_code = self._clean_part(postal_code)
        city = self._clean_part(city)
        country = self._clean_part(country)

        if not any([postal_code, city, country]):
            return None, None

        query_parts = [part for part in (postal_code, city, country) if part]

        query = ", ".join(query_parts)

        if query in self._cache:
            return self._cache[query]

        try:
            location = self.geolocator.geocode(query, exactly_one=True)
            time.sleep(self.delay_seconds)

            if location:
                result = (location.latitude, location.longitude)
            else:

                print(f"Geocoding returned no result for '{query}'")
                result = (None, None)
            self._cache[query] = result
            return result
        except GeopyError as error:
            print(f"Geocoding failed for '{query}': {error}")

        self._cache[query] = (None, None)
        return None, None

    def enrich_location(self, location: dict[str, Any]) -> dict[str, Any]:
        latitude = location.get("latitude")
        longitude = location.get("longitude")

        if latitude is not None and longitude is not None:
            location["coordinates_source"] = "source"
            return location

        lat, lon = self.geocode_location(
            postal_code=location.get("postal_code"),
            city=location.get("city"),
            country=location.get("country"),
        )

        if lat is not None and lon is not None:
            location["latitude"] = lat
            location["longitude"] = lon
            location["coordinates_source"] = "geocoded"
        else:
            location["coordinates_source"] = "missing"

        return location

    def enrich_job(self, job: dict[str, Any]) -> dict[str, Any]:
        locations = job.get("locations", [])

        if not isinstance(locations, list):
            return job
        

        enriched_locations = []
        num_malformed = 0

        for location in locations:
            if not isinstance(location,dict):
                print(f"Skipping malformed location entry (not a dict): {location!r}")
                num_malformed += 1
                continue
            enriched_locations.append(self.enrich_location(location))

        job["locations"] = enriched_locations
        return job, num_malformed

    def enrich_jobs(self, jobs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
        enriched_jobs = []
        total_malformed = 0

        for job in jobs:
            enriched_job, num_malformed = self.enrich_job(job)
            enriched_jobs.append(enriched_job)
            total_malformed += num_malformed

        return enriched_jobs, total_malformed


def enrich_jobs_with_geocoding(
    jobs: list[dict[str, Any]],
    delay_seconds: float = 1.0,
) -> tuple[list[dict[str, Any]], int]:
    geocoder = JobLocationGeocoder(delay_seconds=delay_seconds)
    return geocoder.enrich_jobs(jobs)
