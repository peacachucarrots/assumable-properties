from pydantic import BaseModel

class ListingOut(BaseModel):
    listing_id: int
    address: str
    price: float
    loan_type: str
    mls_status: str