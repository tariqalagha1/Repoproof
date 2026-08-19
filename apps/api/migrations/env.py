"""Alembic env.py — async migration support."""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from src.infrastructure.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    """Prefer DATABASE_URL (set by docker compose / runtime env), fall back to ini."""
    url = os.environ.get("DATABASE_URL")
    if url:
        config.set_main_option("sqlalchemy.url", url)
        return url
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    url = _database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    from sqlalchemy.ext.asyncio import AsyncEngine

    connectable: AsyncEngine = create_async_engine(_database_url())
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
