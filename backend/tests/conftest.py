import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import normalizar_url
from app.db import get_db
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _migrar(url: str) -> None:
    """Recrea el esquema de la BD de pruebas con alembic (downgrade base + upgrade head)."""
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    anterior = {k: os.environ.get(k) for k in ("ALEMBIC_DATABASE_URL", "SEED_MOCK_DATA")}
    os.environ["ALEMBIC_DATABASE_URL"] = url
    os.environ["SEED_MOCK_DATA"] = "false"
    try:
        command.downgrade(cfg, "base")
        command.upgrade(cfg, "head")
    finally:
        for k, v in anterior.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


@pytest.fixture(scope="session")
def engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no está definida")
    url = normalizar_url(url)
    _migrar(url)
    eng = create_engine(url, pool_pre_ping=True)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine):
    """Sesión dentro de una transacción externa que se revierte al terminar cada test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db):
    def _get_db():
        yield db

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
