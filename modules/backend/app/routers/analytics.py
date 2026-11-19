"""Analytics endpoints backed by Open-Meteo weather data."""

import logging
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.services.open_meteo_analytics_service import open_meteo_analytics_service


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)


@router.get("/locations")
async def search_locations(
    name: str = Query(..., min_length=2, max_length=120, description="Place name or postal code"),
) -> Dict[str, Any]:
    """Search Open-Meteo's geocoding index for locations to center on the map."""
    try:
        results = await open_meteo_analytics_service.search_locations(name.strip())
    except httpx.HTTPError as exc:
        logger.warning("Open-Meteo geocoding request failed: %s", exc)
        raise HTTPException(status_code=502, detail="Location search is temporarily unavailable") from exc

    return {"status": "success", "results": results}


@router.get("/weather")
async def get_weather_analytics(
    latitude: float = Query(-1.286389, ge=-90, le=90, description="WGS84 latitude"),
    longitude: float = Query(36.817223, ge=-180, le=180, description="WGS84 longitude"),
    days: int = Query(30, ge=7, le=365, description="Number of calendar days to return"),
) -> Dict[str, Any]:
    """Return chart-ready real weather observations and current conditions."""
    try:
        weather = await open_meteo_analytics_service.get_weather(latitude, longitude, days)
    except httpx.HTTPError as exc:
        logger.warning("Open-Meteo analytics request failed: %s", exc)
        raise HTTPException(status_code=502, detail="Open-Meteo weather data is temporarily unavailable") from exc

    daily = weather["daily"]
    precipitation = [day["precipitation"] or 0.0 for day in daily]
    temperatures = [day["temperature_mean"] for day in daily if day["temperature_mean"] is not None]
    winds = [day["wind_speed_max"] for day in daily if day["wind_speed_max"] is not None]
    et0_values = [day["et0"] or 0.0 for day in daily]

    return {
        "status": "success",
        "data_source": "Open-Meteo",
        "location": {
            "latitude": weather["latitude"],
            "longitude": weather["longitude"],
            "timezone": weather["timezone"],
        },
        "current": weather["current"],
        "summary": {
            "days": len(daily),
            "total_precipitation": round(sum(precipitation), 1),
            "average_temperature": round(sum(temperatures) / len(temperatures), 1) if temperatures else None,
            "rainy_days": sum(value > 0 for value in precipitation),
            "max_wind_speed": round(max(winds), 1) if winds else None,
            "total_et0": round(sum(et0_values), 1),
        },
        "daily": daily,
    }
