from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from db import get_session
from routes.auth import require_auth
from .helpers.schemas import ListingOut, ListingDetail
from .helpers.sql import BASE_LIST_SQL, ORDER_CLAUSE, DETAIL_SQL

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
