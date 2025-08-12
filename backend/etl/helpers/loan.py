import pandas as pd
from etl.maps import LT_MAP

def canon_loan_type(raw):
    if pd.isna(raw):
        return None
    raw = str(raw).strip()
    return LT_MAP.get(raw)