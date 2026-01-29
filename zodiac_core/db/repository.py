from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from zodiac_core.db.session import db, manage_session


class BaseSQLRepository:
    """
    Standard base class for SQL-based repositories.

    Focuses purely on providing a managed database session.
    """

    def __init__(
        self,
        session_factory: Optional[async_sessionmaker[AsyncSession]] = None,
        options: Optional[Any] = None,
    ) -> None:
        """
        Initialize the repository.

        Args:
            session_factory: Optional custom session factory. Fallbacks to db.session_factory.
            options: Optional configuration/options for the repository.
        """
        self._session_factory = session_factory
        self.options = options

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        Async context manager for obtaining a database session.
        Uses the injected factory or the global Zodiac 'db' session logic.
        """
        factory = self._session_factory or db.session_factory
        async with manage_session(factory) as session:
            yield session
