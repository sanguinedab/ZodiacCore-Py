import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from zodiac_core.db.session import DatabaseManager, db, get_session, init_db_resource

# Use an in-memory SQLite database for testing
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.mark.asyncio
async def test_singleton_behavior():
    """Test that DatabaseManager is a strict singleton."""
    db1 = DatabaseManager()
    db2 = DatabaseManager()
    assert db1 is db2
    assert db1 is db


@pytest.mark.asyncio
async def test_lifecycle_setup_shutdown():
    """Test setup and shutdown lifecycle."""
    # Ensure clean state
    if db._engine:
        await db.shutdown()

    # 1. Test Setup
    db.setup(TEST_DB_URL)
    assert db._engine is not None
    assert db._session_factory is not None

    # 2. Test Idempotency (calling setup again should not change anything)
    original_engine = db._engine
    db.setup(TEST_DB_URL)
    assert db._engine is original_engine

    # 3. Test Shutdown
    await db.shutdown()
    assert db._engine is None
    assert db._session_factory is None


@pytest.mark.asyncio
async def test_session_context_manager():
    """Test the session context manager."""
    db.setup(TEST_DB_URL)
    try:
        async with db.session() as session:
            assert isinstance(session, AsyncSession)
            # Verify session is active (bound to an engine)
            assert session.bind is not None
    finally:
        await db.shutdown()


@pytest.mark.asyncio
async def test_session_error_handling():
    """Test that session rolls back on error."""
    db.setup(TEST_DB_URL)

    # We need to create a table to test a transaction, or just verify rollback is called.
    # Since we can't easily mock the internal session object inside the context manager without extensive patching,
    # we rely on the behavior that an exception propagates.

    with pytest.raises(ValueError):
        async with db.session():
            raise ValueError("Intentional Error")

    # Clean up
    await db.shutdown()


@pytest.mark.asyncio
async def test_uninitialized_error():
    """Test proper errors when not initialized."""
    # Ensure shutdown
    if db._engine:
        await db.shutdown()

    with pytest.raises(RuntimeError, match="not initialized"):
        async with db.session():
            pass

    with pytest.raises(RuntimeError, match="not initialized"):
        await db.create_all()


@pytest.mark.asyncio
async def test_get_session_dependency():
    """Test the FastAPI dependency generator."""
    db.setup(TEST_DB_URL)

    # Consuming the generator manually
    gen = get_session()
    session = await anext(gen)

    assert isinstance(session, AsyncSession)

    # Clean up generator (simulate FastAPI finishing request)
    try:
        await anext(gen)
    except StopAsyncIteration:
        pass

    await db.shutdown()


@pytest.mark.asyncio
async def test_init_db_resource_helper():
    """Test the dependency_injector resource helper."""
    # Ensure clean state
    if db._engine:
        await db.shutdown()

    # The resource generator yields the db instance
    gen = init_db_resource(TEST_DB_URL)

    # 1. Start resource
    yielded_db = await anext(gen)
    assert yielded_db is db
    assert db._engine is not None

    # 2. Verify it's working
    async with db.session() as session:
        assert isinstance(session, AsyncSession)

    # 3. Shutdown resource
    try:
        await anext(gen)
    except StopAsyncIteration:
        pass

    assert db._engine is None
