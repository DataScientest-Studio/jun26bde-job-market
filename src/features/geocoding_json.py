from __future__ import annotations

import time
from typing import Any

from geopy.geocoders import Nominatim


class JobLocationGeocoder:
    def __init__(
        self,
        user_agent: str = "job-market-mapper",
        delay_seconds: float = 1.0,
    ) -> None:
        self.geolocator = Nominatim(user_agent=user_agent)
        self.delay_seconds = delay_seconds
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

        query_parts: list[str] = []
        if postal_code:
            query_parts.append(postal_code)
        if city:
            query_parts.append(city)
        if country:
            query_parts.append(country)

        query = ", ".join(query_parts)

        if query in self._cache:
            return self._cache[query]

        try:
            location = self.geolocator.geocode(query, exactly_one=True)
            time.sleep(self.delay_seconds)

            if location:
                result = (location.latitude, location.longitude)
                self._cache[query] = result
                return result
        except TypeError as error:
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

        job["locations"] = [
            self.enrich_location(location)
            for location in locations
            if isinstance(location, dict)
        ]
        return job

    def enrich_jobs(self, jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.enrich_job(job) for job in jobs]


def enrich_jobs_with_geocoding(
    jobs: list[dict[str, Any]],
    delay_seconds: float = 1.0,
) -> list[dict[str, Any]]:
    geocoder = JobLocationGeocoder(delay_seconds=delay_seconds)
    return geocoder.enrich_jobs(jobs)
