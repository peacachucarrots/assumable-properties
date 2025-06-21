from fastapi import FastAPI, Query, Request, Depends
from fastapi_users import schemas as fu_schemas
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from typing import List, Optional

from app.routes import admin, signup, listings
from app.auth import fastapi_users, cookie_backend, current_user, current_admin
from app.models import User
from app.db import db
from app.helpers.formatting import currency
from app.helpers.dicts import LABELS
from app.helpers.classes import ListingOut

app = FastAPI(title="Assumable Listings API")
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["currency"] = currency
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
async def startup() -> None:
    await db.connect()

@app.on_event("shutdown")
async def shutdown() -> None:
    await db.disconnect()

app.include_router(fastapi_users.get_auth_router(cookie_backend), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(fu_schemas.BaseUser), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(), prefix="/auth", tags=["auth"])
app.include_router(admin.router)
app.include_router(signup.router)
app.include_router(listings.router)

@app.get("/listings", response_model=list[ListingOut])
async def listings_api(
    loan_types: List[str] | None,
    max_price: int | None,
    ir35_flag: bool,
    user: User = Depends(current_user),
):
    where_parts: list[str] = []
    params: dict[str, object] = {}

    if loan_types:
        where_parts.append("lo.loan_type = ANY(:lts)")
        params["lts"] = loan_types

    if max_price is not None:
        where_parts.append("lp.price <= :px")
        params["px"] = max_price

    if ir35_flag:
        where_parts.append("lo.interest_rate <= 3.5")

    where_sql = ""
    if where_parts:
        where_sql = "WHERE " + " AND ".join(where_parts)

    # ---------- final SQL ----------
    sql = f"""
          WITH latest_price AS (
            SELECT DISTINCT ON (listing_id)
                   listing_id, price
            FROM   price_history
            ORDER  BY listing_id, effective_date DESC
          )
          SELECT l.listing_id,
                 p.street || ', ' ||
                 p.city || ', ' ||
                 p.state || ' ' ||
                 p.zip AS address,
                 lp.price,
                 lo.loan_type,
                 l.mls_status
          FROM   listing         l
          JOIN   property        p  ON p.property_id  = l.property_id
          JOIN   loan            lo ON lo.property_id = p.property_id
          JOIN   latest_price    lp ON lp.listing_id  = l.listing_id
          {where_sql}
          ORDER  BY lp.price;
        """

    rows = await db.fetch_all(sql, params)
    return [ListingOut(**r) for r in rows]

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def listings_html(
        request: Request,
        loan_type: Optional[List[str]] = Query(default=None),
        max_price: Optional[str] = None,
        ir35: Optional[str] = None,
):
    loan_types = loan_type
    max_price_val = int(max_price) if max_price else None
    ir35_flag = bool(ir35)

    rows = await listings_api(loan_types, max_price_val, ir35_flag)
    return templates.TemplateResponse(
        "listings.html",
        {
            "request": request,
            "rows": rows,
            "loan_types": loan_types,
            "labels": LABELS,
            "max_price": max_price,
            "ir35": ir35_flag,
        },
    )