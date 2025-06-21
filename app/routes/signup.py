from fastapi import APIRouter, Depends, HTTPException
from fastapi_users import schemas
from app.auth import fastapi_users, get_user_db
from app.db import db

router = APIRouter(tags=["auth"])

UserCreate = schemas.BaseUserCreate

@router.post("/signup", response_model=schemas.BaseUser)
async def signup(user: UserCreate, token: str):
    inv = await db.fetch_one(
        "SELECT * FROM invite WHERE token = :tok AND accepted = false "
        "AND expires_at > now()", {"tok": token}
    )
    if not inv:
        raise HTTPException(400, detail="Invalid or used invite token")

    user_obj = await fastapi_users.get_user_manager(get_user_db).create(user)
    # mark invite accepted
    await db.execute("UPDATE invite SET accepted = true WHERE token = :tok", {"tok": token})
    return user_obj