from __future__ import annotations
import os
from typing import Optional, Tuple
import httpx

GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY")

def _score(result: dict) -> int:
    t = (result.get("geometry", {}).get("location_type") or "APPROXIMATE").upper()
    loc_score = {"ROOFTOP": 4, "RANGE_INTERPOLATED": 3, "GEOMETRIC_CENTER": 2, "APPROXIMATE": 1}.get(t, 1)
    partial_penalty = -2 if result.get("partial_match") else 0
    street_bonus = 1 if "street_address" in (result.get("types") or []) else 0
    return loc_score + partial_penalty + street_bonus

async def geocode_address(
        street: str, city: str, state: str, zip_code: str, unit: Optional[str] = None
) -> Optional[Tuple[float, float]]:
    if not GOOGLE_MAPS_KEY:
        return None

    line1 = f"{street}{(' ' + unit) if unit else ''}"
    freeform = f"{line1}, {city}, {state} {zip_code}, USA"

    params = {
        "address": freeform,
        "components": f"country:US|postal_code:{zip_code}",
        "region": "us",
        "key": GOOGLE_MAPS_KEY,
    }

    async with httpx.AsyncClient(timeout=8.0) as client:
        r = await client.get("https://maps.googleapis.com/maps/api/geocode/json", params=params)
        r.raise_for_status()
        data = r.json()

    if data.get("status") != "OK" or not data.get("results"):
        return None

    best = max(data["results"], key=_score)
    loc = best.get("geometry", {}).get("location", {})
    lat, lng = loc.get("lat"), loc.get("lng")
    if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
        return float(lat), float(lng)
    return None