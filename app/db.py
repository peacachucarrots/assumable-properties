# app/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from databases import Database

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://noahhomyak@localhost/assumables",
)

engine = create_engine(DB_URL, echo=False)

class Base(DeclarativeBase):
    pass

db = Database(DB_URL)