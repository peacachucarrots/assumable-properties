import os
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

async_engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session

SCHEMA_SQL = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
async def init_db():
    async with async_engine.begin() as conn:
        await conn.execute(text(SCHEMA_SQL.read_text()))