import os, time
import httpx

GOOGLE_MAPS_KEY = os.getenv("GOOGLE_MAPS_KEY")

def _geo_score(result: dict) -> int:
    t = (result.get("geometry", {}).get("location_type") or "APPROXIMATE").upper()
    loc = {"ROOFTOP": 4, "RANGE_INTERPOLATED": 3, "GEOMETRIC_CENTER": 2, "APPROXIMATE": 1}.get(t, 1)
    partial = -2 if result.get("partial_match") else 0
    bonus = 1 if "street_address" in (result.get("types") or []) else 0
    return loc + partial + bonus

def geocode_address_sync(client: httpx.Client, street: str, city: str, state: str, zip_code: str, unit: str | None = None):
    """
    Returns (lat, lon) or None.
    """
    if not GOOGLE_MAPS_KEY:
        return None
    if not (street and city and state and zip_code):
        return None

    line1 = f"{street}{(' ' + unit) if unit else ''}"
    params = {
        "address": f"{line1}, {city}, {state} {zip_code}, USA",
        "components": f"country:US|postal_code:{zip_code}",
        "region": "us",
        "key": GOOGLE_MAPS_KEY,
    }
    try:
        r = client.get("https://maps.googleapis.com/maps/api/geocode/json", params=params)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return None

    if data.get("status") != "OK" or not data.get("results"):
        return None

    best = max(data["results"], key=_geo_score)
    loc = (best.get("geometry") or {}).get("location") or {}
    lat, lng = loc.get("lat"), loc.get("lng")
    if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
        return float(lat), float(lng)
    return None

class QPSLimiter:
    def __init__(self, qps: float = 10.0):
        self.min_interval = 1.0 / max(qps, 0.1)
        self._last = 0.0
    def wait(self):
        now = time.monotonic()
        delta = now - self._last
        if delta < self.min_interval:
            time.sleep(self.min_interval - delta)
        self._last = time.monotonic()