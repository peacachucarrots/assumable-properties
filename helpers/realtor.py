import re, pandas as pd

SPLIT_REALTOR = re.compile(r'[\/,&]| and ', re.I)

def split_realtors(raw):
    """
    Return a list of clean names.
    Examples:
      "Alice Smith / Bob Jones"  → ["Alice Smith", "Bob Jones"]
      "Jane Doe"                 → ["Jane Doe"]
    """
    if pd.isna(raw):
        return []
    parts = [p.strip() for p in SPLIT_REALTOR.split(str(raw)) if p.strip()]
    return parts