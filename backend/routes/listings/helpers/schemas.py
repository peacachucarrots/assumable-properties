from pydantic import BaseModel, field_validator
from decimal import Decimal
import math
import datetime as dt

class _FiniteFloatModel(BaseModel):
    """Mixin that turns NaN/∞ (float *or* Decimal) into None on every field."""

    @field_validator("*", mode="before")
    def _nan_decimal_to_none(cls, v):
        if v is None:
            return v
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        if isinstance(v, Decimal) and v.is_nan():
            return None
        return v

class ListingOut(_FiniteFloatModel):
    listing_id: int
    address: str
    price: float | None = None
    loan_type: str
    mls_status: str | None = None
    lat: float | None = None
    lon: float | None = None

class ListingDetail(ListingOut):
    beds: int | None
    baths: int | None
    sqft: int | None
    interest_rate: float | None
    balance: float | None
    piti: float | None
    realtor_name: str | None
    date_added: dt.date | None
    mls_link: str | None