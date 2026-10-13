from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy.pool import NullPool
from app.core.config import settings
import ssl
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import re
import os
import sys
import asyncio
import socket


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


def validate_database_url(database_url: str) -> str:
    """Validate and return the database URL."""
    if not database_url:
        print("ERROR: DATABASE_URL is not set!", file=sys.stderr)
        raise ValueError(
            "DATABASE_URL is not set. Please set the DATABASE_URL environment variable "
            "in Render dashboard with a valid PostgreSQL connection string."
        )
    
    # Basic validation
    if not database_url.startswith(("postgresql://", "postgresql+asyncpg://")):
        raise ValueError("DATABASE_URL must start with postgresql:// or postgresql+asyncpg://")
    
    return database_url


async def resolve_hostname(hostname: str, port: int = 5432) -> list[str]:
    """Resolve hostname to IP addresses with retry logic."""
    import aiodns
    
    resolver = aiodns.DNSResolver()
    # Use Google's DNS as fallback
    resolver.nameservers = ['8.8.8.8', '1.1.1.1', '208.67.222.222']
    
    try:
        result = await resolver.query(hostname, 'A')
        return [r.host for r in result]
    except aiodns.error.DNSError as e:
        print(f"DNS resolution failed for {hostname}: {e}", file=sys.stderr)
        # Fallback to system resolver with retries
        for attempt in range(3):
            try:
                loop = asyncio.get_event_loop()
                addrs = await asyncio.get_event_loop().getaddrinfo(
                    hostname, port, family=socket.AF_INET, type=socket.SOCK_STREAM
                )
                return [addr[4][0] for addr in addrs]
            except (socket.gaierror, OSError) as e:
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
    return []


def create_engine_with_ssl(database_url: str):
    """Create async engine with proper SSL configuration for asyncpg."""
    # Validate URL first
    if not database_url:
        raise ValueError(
            "DATABASE_URL is not set. Please set the DATABASE_URL environment variable "
            "in Render dashboard with a valid PostgreSQL connection string."
        )
    
    if not database_url.startswith(("postgresql://", "postgresql+asyncpg://")):
        raise ValueError("DATABASE_URL must start with postgresql:// or postgresql+asyncpg://")
    
    # Parse URL manually to handle postgresql+asyncpg driver
    parsed = urlparse(database_url)
    
    # Validate hostname
    if not parsed.hostname:
        raise ValueError(f"Invalid database URL: missing hostname in {database_url}")
    
    print(f"Connecting to database host: {parsed.hostname}:{parsed.port or 5432}", file=sys.stderr)
    
    # Extract SSL parameters from query string
    query_params = parse_qs(parsed.query)
    sslmode = query_params.pop("sslmode", [None])[0]
    
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
    
    # Rebuild query string without sslmode
    new_query = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
    query_string = urlencode(new_query) if new_query else ""
    
    # Reconstruct URL without sslmode - handle postgresql+asyncpg scheme
    scheme_end = database_url.find("://")
    if scheme_end == -1:
        raise ValueError("Invalid database URL")
    
    scheme = database_url[:scheme_end + 3]  # includes "://"
    rest = database_url[scheme_end + 3:]
    
    # Split path and query
    if "?" in rest:
        path_part, query_part = rest.split("?", 1)
    else:
        path_part = rest
        query_part = ""
    
    # Reconstruct URL without sslmode
    new_query = query_string
    if new_query:
        url_without_ssl = f"{scheme}{path_part}?{query_string}"
    else:
        url_without_ssl = f"{scheme}{path_part}"
    
    connect_args = {}
    if ssl_context:
        connect_args["ssl"] = ssl_context
    
    return create_async_engine(
        url_without_ssl,
        echo=settings.DEBUG,
        poolclass=NullPool if settings.ENVIRONMENT == "test" else None,
        pool_pre_ping=True,
        connect_args=connect_args,
        # Add connection retry logic
        pool_recycle=3600,
        pool_timeout=30,
    )


# Get DATABASE_URL from environment with validation
database_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL
if not database_url:
    print("FATAL: DATABASE_URL environment variable is not set!", file=sys.stderr)
    print("Please set DATABASE_URL in Render dashboard", file=sys.stderr)
    raise ValueError("DATABASE_URL is not set")

print(f"Using DATABASE_URL: {database_url[:50]}...", file=sys.stderr)

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
    # Add retry logic for database initialization
    max_retries = 5
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("Database initialized successfully", file=sys.stderr)
            return
        except Exception as e:
            if attempt < 4:
                wait_time = 2 ** attempt
                print(f"Database init failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...", file=sys.stderr)
                await asyncio.sleep(wait_time)
            else:
                print(f"Failed to initialize database after {max_retries} attempts", file=sys.stderr)
                raise


async def close_db():
    await engine.dispose()


# Tenant context middleware
def set_tenant_context(lodge_id: str):
    from sqlalchemy import text
    return text(f"SET LOCAL app.current_lodge_id = '{lodge_id}'")