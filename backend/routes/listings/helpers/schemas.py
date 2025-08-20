from pydantic import BaseModel, field_validator
from decimal import Decimal
import math
from datetime import date, datetime
from typing import Optional, List

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

class PricePoint(BaseModel):
    price_id: Optional[int] = None
    effective_date: date
    price: float

class ResponseItem(BaseModel):
    response_id: int
    author: Optional[str] = None
    note_text: Optional[str] = None
    created_at: datetime

class ListingOut(_FiniteFloatModel):
    listing_id: int
    address: str
    price: Optional[float] = None
    loan_type: str
    mls_status: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

class ListingDetail(_FiniteFloatModel):
    listing_id: int

    # Address / property
    street: str
    unit: Optional[str] = None
    city: str
    state: str
    zip: str
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    hoa_amount: Optional[float] = None
    hoa_frequency: Optional[str] = None

    # Listing
    date_added: Optional[date] = None
    mls_link: Optional[str] = None
    mls_status: Optional[str] = None
    equity_to_cover: Optional[float] = None
    sent_to_clients: Optional[bool] = None
    investor_ok: Optional[bool] = None

    # Realtor
    realtor_name: str

    # Loan
    loan_type: Optional[str] = None
    interest_rate: Optional[float] = None
    balance: Optional[float] = None
    piti: Optional[float] = None
    loan_servicer: Optional[str] = None
    investor_allowed: Optional[bool] = None

    # Price
    asking_price: Optional[float] = None
    price_history: List[PricePoint] = []

    # Analysis
    analysis_url: Optional[str] = None
    roi_pass: Optional[bool] = None
    done_running_numbers: Optional[bool] = None
    analysis_run_date: Optional[datetime] = None

    # Notes / responses
    responses: List[ResponseItem] = []

class ListingCreate(BaseModel):
    # Address / property
    street: str
    unit: Optional[str] = None
    city: str
    state: str
    zip: str
    beds: Optional[int] = None
    baths: Optional[float] = None
    sqft: Optional[int] = None
    hoa_amount: Optional[float] = None
    hoa_frequency: Optional[str] = None

    # Realtor
    realtor_name: str

    # Listing
    date_added: Optional[str] = None
    mls_link: Optional[str] = None
    mls_status: Optional[str] = None
    sent_to_clients: Optional[bool] = None

    # Loan
    loan_type: Optional[str] = None
    interest_rate: Optional[float] = None
    balance: Optional[float] = None
    piti: Optional[float] = None
    loan_servicer: Optional[str] = None
    investor_allowed: Optional[bool] = None

    # Price
    asking_price: Optional[float] = None

    # Analysis
    analysis_url: Optional[str] = None
    done_running_numbers: Optional[bool] = None
    roi_pass: Optional[bool] = None

    # Notes
    response_from_realtor: Optional[str] = None
    full_response_from_amy: Optional[str] = None
