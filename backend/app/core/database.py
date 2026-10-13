import os
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.core.config import settings

# Embedded SQLite is the default database. Override with DATABASE_URL (full
# SQLAlchemy URL) or SQLITE_PATH (path to the .db file) — e.g. point SQLITE_PATH
# at a Render Persistent Disk mount so data survives redeploys.
DEFAULT_DATABASE_URL = "sqlite+aiosqlite:///./familyman.db"


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


def _resolve_database_url() -> str:
    """Resolve the database URL, ignoring deprecated Postgres values.

    Postgres support was removed (no asyncpg/psycopg driver is installed), so any
    leftover postgres:// URL in the environment is skipped in favour of embedded
    SQLite instead of crashing on a missing driver.
    """
    candidates = (
        os.getenv("DATABASE_URL"),
        os.getenv("SQLITE_PATH"),
        settings.DATABASE_URL,
    )
    for raw in candidates:
        if not raw:
            continue
        url = raw
        # Handle a Render-style "DATABASE_URL=postgresql://..." value.
        if url.startswith("DATABASE_URL="):
            url = url[len("DATABASE_URL=") :]
        # Catches postgres://, postgresql://, postgresql+asyncpg://, etc.
        if url.startswith("postgres"):
            print("Ignoring deprecated Postgres DATABASE_URL; using SQLite.", flush=True)
            continue
        # A bare filesystem path (from SQLITE_PATH) needs the aiosqlite scheme.
        if not url.startswith("sqlite"):
            url = f"sqlite+aiosqlite:///{url}"
        return url
    return DEFAULT_DATABASE_URL


database_url = _resolve_database_url()
print(f"Database engine: {database_url.split('://')[0]}", flush=True)

engine = create_async_engine(
    database_url,
    # SQLite is not safe across threads by default; aiosqlite + FastAPI's
    # threadpool need this disabled.
    connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {},
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables (SQLite has no separate migration step)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database initialized successfully", flush=True)


async def close_db() -> None:
    await engine.dispose()
