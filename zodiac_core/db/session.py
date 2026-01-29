from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

try:
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from sqlmodel import SQLModel
except ImportError as e:
    raise ImportError(
        "SQLModel and SQLAlchemy[asyncio] are required to use the 'zodiac_core.db' module. "
        "Please install it with: pip install 'zodiac-core[sql]'"
    ) from e


@asynccontextmanager
async def manage_session(factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    """
    Standardizes the lifecycle management of an AsyncSession.
    Ensures rollback on error and proper closure.
    """
    session: AsyncSession = factory()
    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


class DatabaseManager:
    """
    Manages the Async Database Engine and Session Factory.
    Implemented as a Strict Singleton to ensure only one Connection Pool exists.

    Integration Examples:

    1. **Native FastAPI (Lifespan + Depends):**

        ```python
        # main.py
        from contextlib import asynccontextmanager
        from fastapi import FastAPI, Depends
        from sqlalchemy.ext.asyncio import AsyncSession
        from zodiac_core.db.session import db, get_session

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            db.setup("sqlite+aiosqlite:///database.db")
            yield
            await db.shutdown()

        app = FastAPI(lifespan=lifespan)

        @app.get("/items")
        async def list_items(session: AsyncSession = Depends(get_session)):
            return {"status": "ok"}
        ```

    2. **Dependency Injector (Using provided init_db_resource):**

        ```python
        # containers.py
        from dependency_injector import containers, providers
        from zodiac_core.db.session import init_db_resource

        class Container(containers.DeclarativeContainer):
            config = providers.Configuration()

            # Use the pre-built resource helper
            db_manager = providers.Resource(
                init_db_resource,
                database_url=config.db.url,
                echo=config.db.echo.as_bool(),
            )
        ```
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engine = None
            cls._instance._session_factory = None
        return cls._instance

    @property
    def engine(self) -> AsyncEngine:
        """Access the underlying SQLAlchemy AsyncEngine."""
        if self._engine is None:
            raise RuntimeError("DatabaseManager is not initialized. Call db.setup() first.")
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Access the global AsyncSession factory."""
        if self._session_factory is None:
            raise RuntimeError("DatabaseManager is not initialized. Call db.setup() first.")
        return self._session_factory

    def setup(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_pre_ping: bool = True,
        connect_args: Optional[dict] = None,
        **kwargs,
    ) -> None:
        """Initialize the Async Engine and Session Factory."""
        if self._engine:
            return

        engine_args = {
            "echo": echo,
            "pool_pre_ping": pool_pre_ping,
            "connect_args": connect_args or {},
            **kwargs,
        }

        if "sqlite" not in database_url:
            engine_args["pool_size"] = pool_size
            engine_args["max_overflow"] = max_overflow

        self._engine = create_async_engine(database_url, **engine_args)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    async def shutdown(self) -> None:
        """Dispose of the engine and close all connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context Manager for obtaining a NEW database session."""
        async with manage_session(self.session_factory) as session:
            yield session

    async def create_all(self) -> None:
        """Create all tables defined in SQLModel metadata."""
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)


# Global instance
db = DatabaseManager()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency for obtaining a database session."""
    async with db.session() as session:
        yield session


async def init_db_resource(
    database_url: str,
    echo: bool = False,
    connect_args: Optional[dict] = None,
    **kwargs,
) -> AsyncGenerator[DatabaseManager, None]:
    """
    A helper for dependency_injector's Resource provider.
    Handles the setup and shutdown lifecycle of the global `db` instance.
    """
    db.setup(database_url=database_url, echo=echo, connect_args=connect_args, **kwargs)
    try:
        yield db
    finally:
        await db.shutdown()
