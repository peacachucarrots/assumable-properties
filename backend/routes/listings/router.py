from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from db.main import get_session
from ..auth.router import require_auth
from .helpers.schemas import ListingOut, ListingDetail, ListingCreate
from .helpers.sql import BASE_LIST_SQL, ORDER_CLAUSE, DETAIL_SQL
from .helpers.functions import _to_date_or_none
from .helpers.geocode import geocode_address

router = APIRouter(prefix="/listings", tags=["listings"])

@router.get("", response_model=List[ListingOut], dependencies=[Depends(require_auth)])
async def list_listings(
        session: AsyncSession = Depends(get_session),
        loan_type: Optional[List[str]] = Query(None)
):
    sql_parts = [BASE_LIST_SQL]
    params: dict[str, object] = {}
    if loan_type:
        sql_parts.append("WHERE lo.loan_type = ANY(:loan_types)")
        params["loan_types"] = loan_type

    sql_parts.append(ORDER_CLAUSE)
    sql = " ".join(sql_parts)
    text_sql = text(sql)

    rows = await session.execute(text_sql, params)
    return [ListingOut(**row._mapping) for row in rows]

@router.get("/{lid}", response_model=ListingDetail, dependencies=[Depends(require_auth)])
async def listing_detail(lid: int, session: AsyncSession = Depends(get_session)):
    row = (await session.execute(DETAIL_SQL, {"lid": lid})).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Listing not found")

    return ListingDetail(**row)

@router.post("", dependencies=[Depends(require_auth)])
async def create_listing(payload: ListingCreate, session: AsyncSession = Depends(get_session)):
    try:
        # Realtor
        res = await session.execute(
            text("""
                INSERT INTO realtor (name)
                VALUES (:n)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING realtor_id
            """),
            {"n": (payload.realtor_name or "Unknown").strip() or "Unknown"}
        )
        realtor_id = res.scalar_one()

        # Property
        res = await session.execute(
            text("""
                INSERT INTO property (street, unit, city, state, zip, beds, baths, sqft, hoa_amount, hoa_frequency)
                VALUES (:street, :unit, :city, :state, :zip, :beds, :baths, :sqft, :hoa_amount, :hoa_frequency)
                ON CONFLICT (street, unit, city, state, zip)
                DO UPDATE SET
                  beds = COALESCE(EXCLUDED.beds, property.beds),
                  baths = COALESCE(EXCLUDED.baths, property.baths),
                  sqft = COALESCE(EXCLUDED.sqft, property.sqft),
                  hoa_amount = COALESCE(EXCLUDED.hoa_amount, property.hoa_amount),
                  hoa_frequency = COALESCE(EXCLUDED.hoa_frequency, property.hoa_frequency)
                RETURNING property_id
            """),
            {
                "street": payload.street.strip(),
                "unit": (payload.unit or None),
                "city": payload.city.strip(),
                "state": (payload.state or "CO").strip().upper(),
                "zip": payload.zip.strip(),
                "beds": payload.beds,
                "baths": payload.baths,
                "sqft": payload.sqft,
                "hoa_amount": payload.hoa_amount,
                "hoa_frequency": payload.hoa_frequency or None,
            }
        )
        property_id = res.scalar_one()

        # Geocode address
        coords = await geocode_address(
            payload.street.strip(),
            payload.city.strip(),
            (payload.state or "CO").strip().upper(),
            payload.zip.strip(),
            (payload.unit or None),
        )
        if coords:
            lat, lon = coords
            await session.execute(
                text("""
                    UPDATE property
                    SET latitude = :lat, longitude = :lon
                    WHERE property_id = :pid
                        AND (latitude IS DISTINCT FROM :lat OR longitude IS DISTINCT FROM :lon)
                """),
                {"pid": property_id, "lat": lat, "lon": lon},
            )

        # Listing
        date_added = _to_date_or_none(payload.date_added)
        asking_price = payload.asking_price
        loan_balance = payload.balance
        equity_to_cover = None
        if asking_price is not None and loan_balance is not None:
            equity = round(asking_price - loan_balance, 2)
            equity_to_cover = max(0.0, equity)

        res = await session.execute(
            text("""
                INSERT INTO listing (property_id, realtor_id, date_added, mls_link, mls_status, equity_to_cover, sent_to_clients)
                VALUES (:pid, :rid, COALESCE(:date_added, CURRENT_DATE), :mls_link, :mls_status, :equity, :sent)
                ON CONFLICT ON CONSTRAINT listing_prop_realtor_link_unique
                DO UPDATE SET
                    date_added = COALESCE(EXCLUDED.date_added, listing.date_added),
                    mls_status = COALESCE(EXCLUDED.mls_status, listing.mls_status),
                    equity_to_cover = COALESCE(EXCLUDED.equity_to_cover, listing.equity_to_cover),
                    sent_to_clients = COALESCE(EXCLUDED.sent_to_clients, listing.sent_to_clients)
                RETURNING listing_id
            """),
            {
                "pid": property_id,
                "rid": realtor_id,
                "date_added": date_added,
                "mls_link": payload.mls_link,
                "mls_status": payload.mls_status,
                "equity": equity_to_cover,
                "sent": bool(payload.sent_to_clients),
            }
        )
        listing_id = res.scalar_one()

        # Price history
        if asking_price is not None:
            await session.execute(
                text("""
                    INSERT INTO price_history (listing_id, effective_date, price)
                    VALUES (:lid, COALESCE(:eff, CURRENT_DATE), :price)
                """),
                {"lid": listing_id, "eff": date_added, "price": asking_price}
            )

        # Loan
        loan_type = payload.loan_type.strip() if isinstance(payload.loan_type, str) and payload.loan_type.strip() else "CONV"
        await session.execute(
            text("""
                INSERT INTO loan (property_id, loan_type, interest_rate, balance, piti, loan_servicer, investor_allowed)
                VALUES (:pid, :loan_type, :rate, :bal, :piti, :servicer, :allowed)
                ON CONFLICT (property_id) DO UPDATE SET
                  loan_type = EXCLUDED.loan_type,
                  interest_rate = EXCLUDED.interest_rate,
                  balance = EXCLUDED.balance,
                  piti = EXCLUDED.piti,
                  loan_servicer = EXCLUDED.loan_servicer,
                  investor_allowed = EXCLUDED.investor_allowed
            """),
            {
                "pid": property_id,
                "loan_type": loan_type,
                "rate": payload.interest_rate,
                "bal": payload.balance,
                "piti": payload.piti,
                "servicer": payload.loan_servicer,
                "allowed": bool(payload.investor_allowed) if payload.investor_allowed is not None else None,
            }
        )

        # Analysis
        if (
            payload.analysis_url
            or payload.done_running_numbers is not None
            or payload.roi_pass is not None
        ):
            await session.execute(
                text("""
                    INSERT INTO analysis (listing_id, url, roi_pass, run_complete)
                    VALUES (:lid, :url, :roi, :done)
                """),
                {
                    "lid": listing_id,
                    "url": payload.analysis_url,
                    "roi": payload.roi_pass,
                    "done": payload.done_running_numbers,
                }
            )

        # Notes
        if payload.response_from_realtor:
            await session.execute(
                text("INSERT INTO response (listing_id, author, note_text) VALUES (:lid, 'Realtor/Seller', :t)"),
                {"lid": listing_id, "t": payload.response_from_realtor.strip()}
            )
        if payload.full_response_from_amy:
            await session.execute(
                text("INSERT INTO response (listing_id, author, note_text) VALUES (:lid, 'Amy', :t)"),
                {"lid": listing_id, "t": payload.full_response_from_amy.strip()}
            )

        await session.commit()
        return {"id": listing_id}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
