import re

MLS_ID_PAT = re.compile(r"(?:mls|listing)[^\d]*(\d{5,})", re.IGNORECASE)
ANY_DIGITS = re.compile(r"(\d{5,})")

def extract_mls_id(link):
    if not isinstance(link, str) or not link.strip():
        return None
    s = link.strip()
    m = MLS_ID_PAT.search(s)
    if m:
        return m.group(1)
    m2 = ANY_DIGITS.search(s)
    if m2:
        return m2.group(1)
    return None