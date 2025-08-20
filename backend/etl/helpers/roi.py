import pandas as pd

ROI_TRUE_PATTERNS = [
    "yes! assumable investor",
    "yes! potential assumable investor",
    "yes! fha",
    "yes! va",
    "yes! conventional",
    "yes assumable investor",
    "yes fha",
    "yes va"
]

def parse_roi_pass_and_category(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return (None, None)
    s = str(val).strip()
    sl = s.lower()
    category = None
    if "assumable investor" in sl:
        category = "Assumable Investor"
    elif "potential assumable investor" in sl:
        category = "Potential Assumable Investor"
    elif "fha" in sl:
        category = "FHA"
    elif "va" in sl:
        category = "VA"
    elif "conventional" in sl or "conv" in sl:
        category = "CONV"

    roi_pass = None
    if any(pat in sl for pat in ROI_TRUE_PATTERNS) or sl.startswith("yes"):
        roi_pass = True
    elif sl.startswith("no"):
        roi_pass = False
    return (roi_pass, category)