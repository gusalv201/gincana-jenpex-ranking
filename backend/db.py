import os
from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.engine import make_url
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não configurada.")

database_url = make_url(DATABASE_URL)
if database_url.drivername != "mysql+asyncmy":
    raise RuntimeError(
        "DATABASE_URL deve usar o driver assíncrono MySQL: mysql+asyncmy://."
    )

async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)
async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def check_database_connection() -> None:
    async with async_engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session() as session:
        yield session
