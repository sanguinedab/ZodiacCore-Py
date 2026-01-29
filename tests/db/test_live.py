from datetime import timezone

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from zodiac_core.db.sql import IntIDModel, UUIDModel

from .utils import DB_URLS, managed_db_session


class Product(UUIDModel, table=True):
    __tablename__ = "test_products"
    name: str
    price: float


class Category(IntIDModel, table=True):
    __tablename__ = "test_categories"
    name: str


@pytest.mark.serial
class TestSQL:
    async def _assert_uuid(self, session: AsyncSession, is_utc: bool = False):
        p1 = Product(name="MacBook Pro", price=2000.0)
        session.add(p1)
        await session.commit()
        await session.refresh(p1)

        assert p1.id is not None
        assert len(str(p1.id)) == 36

        assert p1.created_at is not None
        assert p1.updated_at is not None

        if is_utc:
            assert p1.created_at.tzinfo == timezone.utc

        original_created_at = p1.created_at
        original_updated_at = p1.updated_at

        # Async tests don't like blocking sleep, but for timestamp diff it's needed
        import asyncio

        await asyncio.sleep(1.1)

        p1.name = "MacBook Air"
        session.add(p1)
        await session.commit()
        await session.refresh(p1)

        # Created_at should NOT change
        assert p1.created_at == original_created_at
        # Updated_at SHOULD change (triggered by event listener)
        assert p1.updated_at > original_updated_at

    async def _assert_id(self, engine, session: AsyncSession):
        c1 = Category(name="Electronics")
        session.add(c1)
        await session.commit()
        await session.refresh(c1)

        assert isinstance(c1.id, int)
        assert c1.id >= 1

        # Raw insert into Category
        async with engine.connect() as conn:
            await conn.execute(text("INSERT INTO test_categories (name) VALUES ('Books')"))
            await conn.commit()

        # Commit current session to end current transaction and see new data in the next query
        await session.commit()

        res = await session.execute(select(Category).where(Category.name == "Books"))
        c2 = res.scalar_one()

        assert c2.created_at is not None
        assert c2.updated_at is not None

    @pytest.mark.parametrize("name,url,connect_args", DB_URLS)
    @pytest.mark.asyncio
    async def test_db_lifecycle(self, name, url, connect_args):
        """
        Test DB lifecycle across different engines:
        DDL -> Insert -> Verify Fields (ID/Time) -> Update -> Verify Time Change
        """
        async with managed_db_session(url, connect_args) as (engine, session):
            await self._assert_uuid(session, name == "postgresql")
            await self._assert_id(engine, session)
