import re, pandas as pd
from .type_conversion import to_decimal

def parse_hoa_amount_and_freq(val):
    """Return (amount, frequency) where frequency in {'Monthly','Quarterly','Semi-Annual','Annual'}"""
    if val is None or (isinstance(val, float) and pd.isna(val)): return (None, None)
    s = str(val).strip()
    if not s or s.lower() in {"none","no hoa","n/a","na","0"}: return (None, None)
    amount = to_decimal(s)
    if amount is None:
        amount = to_decimal(re.sub(r"[^\d.\-]", "", s))
    freq = "Monthly"
    sl = s.lower()
    if "quarter" in sl: freq = "Quarterly"
    elif "semi" in sl:  freq = "Semi-Annual"
    elif "annual" in sl or "year" in sl: freq = "Annual"
    return (amount, freq)