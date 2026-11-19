"""Open-Meteo adapter used by the analytics dashboard."""

from datetime import date, timedelta
from typing import Any, Dict, List

import httpx


FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
DAILY_VARIABLES = (
    "temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
    "precipitation_sum,precipitation_hours,wind_speed_10m_max,"
    "et0_fao_evapotranspiration,weather_code"
)


class OpenMeteoAnalyticsService:
    """Fetch and normalize daily weather data for one dashboard location."""

    async def get_weather(self, latitude: float, longitude: float, days: int) -> Dict[str, Any]:
        today = date.today()
        forecast_days = min(days, 93)
        forecast_params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": DAILY_VARIABLES,
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m",
            "past_days": forecast_days - 1,
            "forecast_days": 1,
            "timezone": "auto",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            forecast = await self._request(client, FORECAST_URL, forecast_params)
            records = self._daily_records(forecast.get("daily", {}))

            # The forecast endpoint serves at most 92 historical days plus today.
            # Use Open-Meteo's archive for older 6- and 12-month data.
            if days > forecast_days:
                archive_end = today - timedelta(days=forecast_days)
                archive_start = today - timedelta(days=days - 1)
                archive_params = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "daily": DAILY_VARIABLES,
                    "start_date": archive_start.isoformat(),
                    "end_date": archive_end.isoformat(),
                    "timezone": "auto",
                }
                archive = await self._request(client, ARCHIVE_URL, archive_params)
                records = self._daily_records(archive.get("daily", {})) + records

        records = sorted({record["date"]: record for record in records}.values(), key=lambda record: record["date"])
        return {
            "latitude": forecast.get("latitude", latitude),
            "longitude": forecast.get("longitude", longitude),
            "timezone": forecast.get("timezone", "auto"),
            "current": forecast.get("current", {}),
            "daily": records,
        }

    @staticmethod
    async def _request(client: httpx.AsyncClient, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise httpx.HTTPStatusError(
                payload.get("reason", "Open-Meteo rejected the request"),
                request=response.request,
                response=response,
            )
        return payload

    @staticmethod
    def _daily_records(daily: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        dates = daily.get("time", [])
        fields = {
            "temperature_max": "temperature_2m_max",
            "temperature_min": "temperature_2m_min",
            "temperature_mean": "temperature_2m_mean",
            "precipitation": "precipitation_sum",
            "precipitation_hours": "precipitation_hours",
            "wind_speed_max": "wind_speed_10m_max",
            "et0": "et0_fao_evapotranspiration",
            "weather_code": "weather_code",
        }
        records: List[Dict[str, Any]] = []
        for index, day in enumerate(dates):
            record: Dict[str, Any] = {"date": day}
            for name, field in fields.items():
                values = daily.get(field, [])
                value = values[index] if index < len(values) else None
                record[name] = float(value) if value is not None else None
            records.append(record)
        return records


open_meteo_analytics_service = OpenMeteoAnalyticsService()
