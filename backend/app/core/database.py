from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import event
from sqlalchemy.pool import NullPool
from sqlalchemy.engine import URL
from app.core.config import settings
import ssl


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


def create_engine_with_ssl(database_url: str):
    """Create async engine with proper SSL configuration for asyncpg."""
    url = URL.create(database_url)
    
    # Extract SSL parameters from query string
    query = dict(url.query) if url.query else {}
    sslmode = query.pop("sslmode", None)
    
    # Create SSL context if needed
    ssl_context = None
    if sslmode in ("require", "verify-ca", "verify-full"):
        ssl_context = ssl.create_default_context()
        if sslmode == "verify-full":
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
        elif sslmode == "verify-ca":
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_REQUIRED
        else:  # require
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
    
    # Rebuild URL without sslmode
    url_without_ssl = URL.create(
        drivername=url.drivername,
        username=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        database=url.database,
        query=query,
    )
    
    connect_args = {}
    if ssl_context:
        connect_args["ssl"] = ssl_context
    
    return create_async_engine(
        url_without_ssl,
        echo=settings.DEBUG,
        poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


engine = create_engine_with_ssl(settings.DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    await engine.dispose()


# Tenant context middleware
def set_tenant_context(lodge_id: str):
    from sqlalchemy import text
    return text(f"SET LOCAL app.current_lodge_id = '{lodge_id}'")