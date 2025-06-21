# app/auth.py
import uuid, os
from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi_users import FastAPIUsers, BaseUserManager, UUIDIDMixin, schemas
from fastapi_users.authentication import CookieTransport, JWTStrategy, AuthenticationBackend
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from pydantic import EmailStr

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db import DB_URL, db              # async Database
from app.models import User
from app.db import engine                  # sync engine for migrations

# ------------------------------------------------------------------
# Database session for fastapi-users (async SQLAlchemy session)
# ------------------------------------------------------------------
async_engine = create_async_engine(
    DB_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
)
AsyncSessionLocal = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# ------------------------------------------------------------------
# User database adapter
# ------------------------------------------------------------------
async def get_user_db(session: Annotated[AsyncSession, Depends(get_async_session)]):
    yield SQLAlchemyUserDatabase(session, User)

# ------------------------------------------------------------------
# UserManager
# ------------------------------------------------------------------
SECRET = os.getenv("JWT_SECRET", "CHANGE_ME")

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret   = SECRET

    async def on_after_register(self, user: User, request=None):
        print(f"User {user.id} has registered.")

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)

# ------------------------------------------------------------------
# Auth back-end (JWT in http-only cookie)
# ------------------------------------------------------------------
# 1️⃣  transport (how the token travels)
cookie_transport = CookieTransport(
    cookie_name="assumable_auth",
    cookie_max_age=3600,
)

# 2️⃣  strategy (sign / verify)
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)

# 3️⃣  backend  ➜  give it a name + glue the two parts
cookie_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

# 4️⃣  FastAPIUsers gets a list of back-ends
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [cookie_backend],          # ← list of AuthenticationBackend instances
)

# ------------------------------------------------------------------
# Dependencies to protect routes
# ------------------------------------------------------------------
current_user  = fastapi_users.current_user(active=True, verified=True)
def current_admin(user: Annotated[User, Depends(current_user)]):
    if not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return user