# app/routes/listings.py
from fastapi import HTTPException, APIRouter, Request, Depends
from typing import Optional
from app.models import User
from app.auth import current_user
from app.db import db
from fastapi.templating import Jinja2Templates

from app.helpers.formatting import currency
from app.helpers.dicts import LABELS

templates = Jinja2Templates(directory="app/templates")
templates.env.filters["currency"] = currency

router = APIRouter(
    tags=["listings"],
)

# ---------- SQL helper ----------
DETAIL_SQL = """
SELECT
    l.listing_id,
    p.street  || ', ' || p.city || ', ' || p.state || ' ' || p.zip AS address,
    lp.price,
    lo.loan_type,
    lo.interest_rate,
    lo.balance,
    lo.piti,
    p.beds,
    p.baths,
    p.sqft,
    l.mls_status,
    l.date_added,
    r.name AS realtor_name,
    l.mls_link
FROM   listing      l
JOIN   property     p  ON p.property_id  = l.property_id
JOIN   realtor      r  ON r.realtor_id   = l.realtor_id
JOIN   loan         lo ON lo.property_id = p.property_id
LEFT   JOIN LATERAL (          -- latest price
    SELECT price
    FROM   price_history ph
    WHERE  ph.listing_id = l.listing_id
    ORDER  BY effective_date DESC
    LIMIT 1
) lp ON true
WHERE  l.listing_id = :lid
"""

@router.get("/listing/{lid}", include_in_schema=False)
async def listing_detail(
    request: Request,
    lid: int,
):
    row = await db.fetch_one(DETAIL_SQL, {"lid": lid})
    if not row:
        raise HTTPException(status_code=404, detail="Listing not found")

    return templates.TemplateResponse(
        "listing_detail.html",
        {"request": request, "row": row, "labels": LABELS},
    )