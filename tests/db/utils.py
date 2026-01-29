import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

# Default local development URLs
DEFAULT_PG_URL = "postgresql+asyncpg://postgres:@localhost:5432/zodiac_test"
DEFAULT_MYSQL_URL = "mysql+aiomysql://root:root@localhost:3306/zodiac_test"

DB_URLS = [
    ("sqlite", "sqlite+aiosqlite:///:memory:", None),
    (
        "postgresql",
        os.getenv("POSTGRES_URL", DEFAULT_PG_URL),
        {"server_settings": {"timezone": "utc"}},
    ),
    (
        "mysql",
        os.getenv("MYSQL_URL", DEFAULT_MYSQL_URL),
        None,
    ),
]


@asynccontextmanager
async def managed_db_session(url, connect_args=None):
    """Manage the lifecycle of an async database session."""
    extras = dict(connect_args=connect_args) if connect_args else {}
    engine = create_async_engine(url, **extras)

    try:
        # Async DDL needs run_sync
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
            await conn.run_sync(SQLModel.metadata.create_all)

        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            yield engine, session
    finally:
        await engine.dispose()
