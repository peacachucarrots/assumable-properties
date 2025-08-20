from datetime import date

def _to_date_or_none(v) -> date | None:
    if v is None:
        return None
    if isinstance(v, date):
        return v
    s = str(v).strip()
    if not s:
        return None
    return date.fromisoformat(s[:10])