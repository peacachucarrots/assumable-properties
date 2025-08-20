import re

STATE_RE = re.compile(r"\b([A-Z]{2})\s+(\d{5}(?:-\d{4})?)\b")
UNIT_PATTERNS = re.compile(r"\b(?:Apt|Unit|#|Ste|Suite)\s*([A-Za-z0-9\-]+)", re.IGNORECASE)

def parse_address(addr):
    if not isinstance(addr, str):
        return None, None, None, None, None
    raw = addr.strip()
    parts = [p.strip() for p in raw.split(",")]
    street, unit, city, state, zip_code = None, None, None, None, None
    if len(parts) >= 3:
        street = parts[0]
        city = parts[-2]
        st_zip = parts[-1]
        m = STATE_RE.search(st_zip)
        if m:
            state, zip_code = m.group(1), m.group(2)
        else:
            tokens = st_zip.split()
            if len(tokens) == 1 and len(tokens[0]) == 2:
                state = tokens[0]
            elif len(tokens) >= 2 and len(tokens[0]) == 2:
                state = tokens[0]
                zip_code = tokens[1]
    elif len(parts) == 2:
        street = parts[0]
        st_zip = parts[1]
        m = STATE_RE.search(st_zip)
        if m:
            state, zip_code = m.group(1), m.group(2)
            city = st_zip[:m.start()].strip().rstrip(",")
        else:
            city = st_zip
    if street:
        um = UNIT_PATTERNS.search(street)
        if um:
            unit = um.group(0).replace("Suite","Ste")
            street = UNIT_PATTERNS.sub("", street).replace("  ", " ").strip()
    return street, unit, city, state, zip_code