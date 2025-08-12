import re, pandas as pd
from typing import Optional, Dict

# pre-compile once
ADDR_RE = re.compile(
    r'^(?P<street>.+?),\s+'
    r'(?P<city>[^,]+),\s+'
    r'(?P<state>[A-Z]{2})\s+'
    r'(?P<zip>\d{5})(?:-\d{4})?$'
)

def split_address(raw: str) -> Optional[Dict[str, str]]:
    """
    Return {'street','city','state','zip'} or None if the line doesn't match.
    Keeps the unit (#102) inside 'street' so no info is lost.
    """
    m = ADDR_RE.match(raw.strip())
    if not m:
        return None
    parts = m.groupdict()
    # normalise capitalisation if you like:
    parts["city"] = parts["city"].title()
    return parts


_Q    = re.compile(r'\$?(\d[\d,.]*)\s*Quarterly', re.I)
_SEMI = re.compile(r'\$?(\d[\d,.]*)\s*Semi[- ]*Annual', re.I)
_ANNU = re.compile(r'\$?(\d[\d,.]*)\s*Annual', re.I)
_MON  = re.compile(r'\$?(\d[\d,.]*)\s*Monthly?', re.I)

def _sum_matches(pattern, text):
    return sum(float(m.replace(',', '')) for m in pattern.findall(text))

def parse_hoa(raw):
    """
    Return HOA in $/month (float) or None.

    • Handles multiple occurrences of each period, e.g.
      "HOA 1 Dues: $52 Quarterly & HOA 2 Dues: $43 Quarterly"
    • Still works for single Monthly / Semi-Annual / Annual values
    • Falls back to plain number → treated as Monthly
    """
    if pd.isna(raw):
        return None
    s = str(raw)

    # 1. Sum each period type separately
    q_total   = _sum_matches(_Q,    s)
    semi_total= _sum_matches(_SEMI, s)
    a_total   = _sum_matches(_ANNU, s)
    m_total   = _sum_matches(_MON,  s)

    # 2. Convert to monthly dollars
    monthly = (
        m_total +                 # already monthly
        q_total   / 3.0 +         # quarterly → /3
        semi_total/ 6.0 +         # semi-annual → /6
        a_total   /12.0           # annual → /12
    )

    if monthly:
        return monthly            # float > 0

    # 3. Plain "$123" or "123"
    try:
        return float(s.lstrip('$').replace(',', ''))
    except ValueError:
        print("⚠️  HOA unparseable:", raw)
        return None

def n2none(v, cast=int):
    """Return cast(v) unless v is NaN / empty, else None."""
    if pd.isna(v):
        return None
    return cast(v) if cast else v