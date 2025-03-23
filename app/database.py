from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import  DeclarativeBase
import os


"""
sqlite+aiosqlite:///./sales.db or postgresql+asyncpg://postgres:PG/eng1102493@localhost:5432/shoppingCart 
for local server"
"""


DATABASE_URL = "postgresql+asyncpg://postgres:PG/eng1102493@localhost:5432/shoppingCart"

async_engine = create_async_engine(DATABASE_URL)

async_SessionLocal = async_sessionmaker(autoflush=False, bind=async_engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
