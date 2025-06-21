# app/models.py
import uuid
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import mapped_column
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID

from app.db import Base

class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = 'user'

class Invite(Base):
    __tablename__ = "invite"

    token = mapped_column(String, primary_key=True)
    email = mapped_column(String, unique=True, nullable=False)
    created_at = mapped_column(DateTime)
    expires_at = mapped_column(DateTime)
    accepted = mapped_column(Boolean, default=False)