"""API client for Bright Sky weather data."""

from __future__ import annotations

from asyncio import timeout
from datetime import date, timedelta
from typing import Any

from aiohttp import ClientSession

BASE_URL = "https://api.brightsky.dev"


class BrightSkyClient:
    """Small API client for Bright Sky."""

    def __init__(
        self,
        session: ClientSession,
        latitude: float,
        longitude: float,
        timeout: int,
    ) -> None:
        self._session = session
        self._latitude = latitude
        self._longitude = longitude
        self._timeout = timeout

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        """GET helper with timeout and error handling."""
        url = f"{BASE_URL}{path}"
        async with timeout(self._timeout):
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def async_fetch_all(
        self,
        history_days: int,
        forecast_days: int,
    ) -> dict[str, Any]:
        """Fetch current weather and historical+forecast timeline."""
        today = date.today()
        start = today - timedelta(days=history_days)
        end = today + timedelta(days=forecast_days)

        query = {
            "lat": self._latitude,
            "lon": self._longitude,
            "date": start.isoformat(),
            "last_date": end.isoformat(),
        }

        timeline = await self._get("/weather", query)
        current = await self._get(
            "/current_weather",
            {"lat": self._latitude, "lon": self._longitude},
        )

        return {
            "timeline": timeline,
            "current": current,
        }
