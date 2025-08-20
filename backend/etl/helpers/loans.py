import pandas as pd
from decimal import Decimal

from .type_conversion import to_decimal

def map_loan_type(s):
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    v = str(s).strip().upper()
    v = v.replace("NON-VETERAN", "NON VETERAN").replace("NONVETERAN","NON VETERAN")
    if "NON" in v and "VA" in v:
        return "NVVA"
    if v == "NON VETERAN VA":
        return "NVVA"
    if "FHA" in v:
        return "FHA"
    if v == "VA":
        return "VA"
    if "CONV" in v or "CONVENTIONAL" in v:
        return "CONV"
    if "MAYBE" in v and "VA" in v:
        return "Maybe_NVVA"
    return None

def normalize_rate(val):
    d = to_decimal(val)
    if d is None: return None
    return (d*100).quantize(Decimal("0.001")) if d <= Decimal("0.5") else d.quantize(Decimal("0.001"))
