"""Async SQLAlchemy engine and session setup."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import get_settings


def get_engine():
    """Create async SQLAlchemy engine."""
    settings = get_settings()
    return create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
    )


engine = get_engine()
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """Yield an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
