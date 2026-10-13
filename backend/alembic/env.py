import asyncio
import sys
import os
import ssl
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine
from alembic import context
from urllib.parse import urlparse, parse_qs, urlencode

sys.path.append(".")

from app.core.config import settings
from app.core.models import Base

config = context.config


def build_database_url(database_url: str):
    """Build database URL with sslmode removed from query string."""
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    sslmode = query_params.pop("sslmode", [None])[0]

    # Rebuild query string without sslmode
    new_query = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
    query_string = "&".join(f"{k}={v}" for k, v in new_query.items()) if new_query else ""

    # Reconstruct URL without sslmode
    new_parsed = parsed._replace(query=query_string)
    url_without_ssl = parsed._replace(query=query_string).geturl()

    return url_without_ssl


def get_ssl_context(database_url: str):
    """Extract SSL context from database URL."""
    parsed = urlparse(database_url)
    query_params = parse_qs(parsed.query)
    sslmode = query_params.get("sslmode", [None])[0]

    if sslmode not in ("require", "verify-ca", "verify-full"):
        return None

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
    return ssl_context


# Get DATABASE_URL from environment variable (set by Render)
database_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL
if database_url:
    # Build URL without sslmode for sqlalchemy.url
    clean_url = build_database_url(database_url)
    config.set_main_option("sqlalchemy.url", clean_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from app.core.config import settings
from app.core.models import Base

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    # Get the original DATABASE_URL for SSL context
    raw_database_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL
    ssl_context = get_ssl_context(raw_database_url)

    # Build clean URL for engine
    clean_url = build_database_url(raw_database_url)

    connect_args = {}
    if ssl_context:
        connect_args["ssl"] = ssl_context

    # Create engine with SSL context via connect_args
    connectable = create_async_engine(
        build_database_url(raw_database_url),
        poolclass=pool.NullPool,
        connect_args={"ssl": ssl_context} if ssl_context else {},
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    await run_async_migrations()


# Always run online migrations (Render has DB connectivity)
run_migrations_online()