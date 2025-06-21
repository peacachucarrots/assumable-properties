from fastapi import APIRouter, Depends, HTTPException
from pydantic import EmailStr
import secrets, datetime as dt

from app.db import db
from app.auth import current_admin  # dependency that allows admins only
from app.email import send_invite_email  # your helper that actually sends

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(current_admin)],
)

@router.post("/invite")
async def create_invite(email: EmailStr):
    token = secrets.token_urlsafe(32)
    await db.execute(
        """
        INSERT INTO invite(token, email, expires_at)
        VALUES (:tok, :em, now() + interval '7 days')
        ON CONFLICT (email) DO UPDATE
          SET token      = :tok,
              created_at = now(),
              expires_at = now() + interval '7 days',
              accepted   = false
        """,
        {"tok": token, "em": email.lower()},
    )
    link = f"http://127.0.0.1:8000/signup?token={token}"
    await send_invite_email(email, link)
    return {"sent": True}