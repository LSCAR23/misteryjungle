import os

from alembic import context
from sqlalchemy import create_engine, pool

from app.config import get_settings, normalizar_url
from app.db import Base

try:
    import app.models  # noqa: F401  (registra las tablas en Base.metadata)
except ImportError:
    pass

config = context.config
target_metadata = Base.metadata


def _url() -> str:
    # Los tests fijan ALEMBIC_DATABASE_URL para migrar la BD de pruebas
    url = os.environ.get("ALEMBIC_DATABASE_URL")
    return normalizar_url(url) if url else get_settings().database_url


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
