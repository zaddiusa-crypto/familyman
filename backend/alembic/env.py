import asyncio
import sys
import os
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

sys.path.append(".")

from app.core.config import settings
from app.core.models import Base

config = context.config

# Get DATABASE_URL from environment variable (set by Render)
database_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

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
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# Check if we're in offline mode (compatible with different alembic versions)
def is_offline_mode():
    # Try multiple approaches for different alembic versions
    try:
        # Standard alembic API (most versions)
        return context.is_offline()
    except AttributeError:
        pass
    
    try:
        # Some versions expose it on the context object
        return context.get_context().is_offline
    except (AttributeError, Exception):
        pass
    
    try:
        # Check alembic version for API differences
        import alembic
        version = tuple(map(int, alembic.__version__.split('.')[:2]))
        if version >= (1, 13):
            # Newer alembic might have different API
            return context.get_context().is_offline
    except Exception:
        pass
    
    # Default to online mode for deployment (Render has DB access)
    return False

if is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()