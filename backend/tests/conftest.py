import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
import uuid

from sqlalchemy import create_engine, make_url, text
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
    """Crea una BD temporal propia de esta ejecución (así corridas en paralelo no chocan)."""
    base = os.environ.get("TEST_DATABASE_URL")
    if not base:
        pytest.skip("TEST_DATABASE_URL no está definida")
    base_url = make_url(normalizar_url(base))
    nombre = f"{base_url.database}_{uuid.uuid4().hex[:8]}"
    admin = create_engine(base_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'CREATE DATABASE "{nombre}"'))
    url = base_url.set(database=nombre).render_as_string(hide_password=False)
    eng = None
    try:
        _migrar(url)
        eng = create_engine(url, pool_pre_ping=True)
        yield eng
    finally:
        if eng is not None:
            eng.dispose()
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{nombre}" WITH (FORCE)'))
        admin.dispose()


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


# --- fixtures de autenticacion (B6) ---
import uuid as _uuid  # noqa: E402

from app.enums import Rol  # noqa: E402
from app.models import Usuario  # noqa: E402
from app.security import create_access_token, hash_password  # noqa: E402


@pytest.fixture
def make_user(db):
    """Fabrica de usuarios via ORM: make_user(rol=Rol.EMPLEADO, password=..., username=None, activo=True)."""

    def _make(rol=Rol.EMPLEADO, password="secreto1", username=None, activo=True):
        user = Usuario(
            username=username or f"t_{_uuid.uuid4().hex[:10]}",
            password_hash=hash_password(password),
            rol=Rol(rol),
            activo=activo,
        )
        db.add(user)
        db.flush()
        return user

    return _make


@pytest.fixture
def admin_headers(make_user):
    u = make_user(rol=Rol.ADMIN)
    return {"Authorization": f"Bearer {create_access_token(u.id, u.rol)}"}


@pytest.fixture
def empleado_headers(make_user):
    u = make_user(rol=Rol.EMPLEADO)
    return {"Authorization": f"Bearer {create_access_token(u.id, u.rol)}"}
