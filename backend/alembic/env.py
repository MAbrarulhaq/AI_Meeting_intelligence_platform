"""
env.py

Alembic's environment script. Two deliberate choices here:
1. The database URL comes from app.config (your .env), not from a
   second copy hardcoded in alembic.ini — one source of truth.
2. `import app.models` before referencing Base.metadata, so every
   model is registered on it before Alembic inspects it for
   autogenerate — otherwise tables defined in modules that were never
   imported would be silently invisible to `alembic revision --autogenerate`.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import every model so they're all registered on Base.metadata.
import app.models  # noqa: F401
from app.config import require_database_url
from app.database.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Single source of truth for the DB URL: app.config (reads .env),
# not a second copy pasted into alembic.ini.
database_url = require_database_url().replace("%", "%%")
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate SQL scripts without a live DB connection (`alembic upgrade --sql`)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database connection (the normal path)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
