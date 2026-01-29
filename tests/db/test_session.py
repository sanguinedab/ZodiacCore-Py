from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from zodiac_core.db.session import DatabaseManager, db, get_session, init_db_resource, manage_session

from .utils import DB_URLS


class TestDatabaseManager:
    """Tests for the DatabaseManager singleton and its lifecycle."""

    @pytest.mark.asyncio
    async def test_singleton_behavior(self):
        """Ensure DatabaseManager is a strict singleton."""
        db1 = DatabaseManager()
        db2 = DatabaseManager()
        assert db1 is db2
        assert db1 is db

    @pytest.mark.asyncio
    async def test_property_guards(self):
        """Ensure engine and factory raise error if accessed before setup."""
        if db._engine:
            await db.shutdown()

        with pytest.raises(RuntimeError, match="DatabaseManager is not initialized"):
            _ = db.engine

        with pytest.raises(RuntimeError, match="DatabaseManager is not initialized"):
            _ = db.session_factory

    @pytest.mark.parametrize("name, url, connect_args", DB_URLS)
    @pytest.mark.asyncio
    async def test_lifecycle_setup_shutdown(self, name, url, connect_args):
        """Verify setup, idempotency, and shutdown state across different DBs."""
        if db._engine:
            await db.shutdown()

        # 1. Setup
        db.setup(url, connect_args=connect_args)
        assert db.engine is not None
        assert db.session_factory is not None

        # 2. Idempotency
        original_engine = db.engine
        db.setup(url, connect_args=connect_args)
        assert db.engine is original_engine

        # 3. Shutdown
        await db.shutdown()
        assert db._engine is None
        assert db._session_factory is None


class TestSessionManagement:
    """Tests for session lifecycle handling and helper functions."""

    @pytest.mark.asyncio
    async def test_manage_session_success(self):
        """Verify manage_session handles normal execution flow."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_factory = MagicMock(return_value=mock_session)

        async with manage_session(mock_factory) as session:
            assert session == mock_session

        mock_session.close.assert_awaited_once()
        mock_session.rollback.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_manage_session_error(self):
        """Verify manage_session performs rollback on exception."""
        mock_session = AsyncMock(spec=AsyncSession)
        mock_factory = MagicMock(return_value=mock_session)

        with pytest.raises(ValueError, match="Database Error"):
            async with manage_session(mock_factory):
                raise ValueError("Database Error")

        mock_session.rollback.assert_awaited_once()
        mock_session.close.assert_awaited_once()

    @pytest.mark.parametrize("name, url, connect_args", DB_URLS)
    @pytest.mark.asyncio
    async def test_singleton_session_context(self, name, url, connect_args):
        """Verify the global db.session() works across different DBs."""
        if db._engine:
            await db.shutdown()

        db.setup(url, connect_args=connect_args)
        try:
            async with db.session() as session:
                assert isinstance(session, AsyncSession)
                from sqlalchemy import text

                await session.execute(text("SELECT 1"))
        finally:
            await db.shutdown()


class TestDependencyIntegration:
    """Tests for framework-specific dependency providers."""

    @pytest.mark.parametrize("name, url, connect_args", DB_URLS)
    @pytest.mark.asyncio
    async def test_init_db_resource_lifecycle(self, name, url, connect_args):
        """Verify dependency_injector resource provider manages full lifecycle."""
        if db._engine:
            await db.shutdown()

        gen = init_db_resource(url, connect_args=connect_args)
        try:
            yielded_db = await anext(gen)
            assert yielded_db is db
            assert db._engine is not None
        finally:
            await gen.aclose()
            # Explicit check after cleanup
            assert db._engine is None

    @pytest.mark.parametrize("name, url, connect_args", DB_URLS)
    @pytest.mark.asyncio
    async def test_get_session_fastapi_dependency(self, name, url, connect_args):
        """Verify FastAPI get_session dependency works across different DBs."""
        if db._engine:
            await db.shutdown()

        db.setup(url, connect_args=connect_args)
        gen = get_session()
        try:
            session = await anext(gen)
            assert isinstance(session, AsyncSession)
            from sqlalchemy import text

            await session.execute(text("SELECT 1"))
        finally:
            await gen.aclose()
            await db.shutdown()
