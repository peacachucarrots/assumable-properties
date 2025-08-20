import pandas as pd
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from dateutil import parser as dateparser

def to_decimal(val):
    if val is None or (isinstance(val, float) and pd.isna(val)) or (isinstance(val, str) and not val.strip()):
        return None
    s = str(val).strip().replace(",", "").replace("$", "")
    if s.endswith("%"):
        try:
            return Decimal(s[:-1])
        except InvalidOperation:
            return None
    try:
        return Decimal(s)
    except InvalidOperation:
        s = s.replace("%","")
        try:
            return Decimal(s)
        except InvalidOperation:
            return None

def to_int(val):
    if pd.isna(val) or val is None or (isinstance(val, str) and not val.strip()):
        return None
    try:
        return int(float(str(val).replace(",","").strip()))
    except Exception:
        return None

def to_float(val):
    d = to_decimal(val)
    if d is None:
        return None
    try:
        return d.quantize(Decimal("0.0"))
    except Exception:
        return d

def to_date(val):
    if pd.isna(val) or val is None or (isinstance(val, str) and not val.strip()):
        return None
    if isinstance(val, (datetime, date)):
        return val.date() if isinstance(val, datetime) else val
    try:
        return dateparser.parse(str(val)).date()
    except Exception:
        return None