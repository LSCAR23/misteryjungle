"""usuarios iniciales (seed)

Revision ID: 0002
Revises: 0001
"""
import os

import bcrypt
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

USUARIOS = [
    ("Oscar", "empleado"),
    ("Daniel", "empleado"),
    ("Ivan", "admin"),
    ("Fabian", "admin"),
]


def upgrade() -> None:
    pw = os.environ.get("SEED_PASSWORD")
    if not pw:
        raise RuntimeError(
            "Falta la variable de entorno SEED_PASSWORD para crear los usuarios iniciales"
        )

    bind = op.get_bind()
    insert = sa.text(
        "INSERT INTO usuarios (id, username, password_hash, rol, activo) "
        "VALUES (gen_random_uuid(), :u, :h, :r, true)"
    )
    for username, rol in USUARIOS:
        h = bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12)).decode()
        bind.execute(insert, {"u": username, "h": h, "r": rol})


def downgrade() -> None:
    op.get_bind().execute(
        sa.text("DELETE FROM usuarios WHERE username IN ('Oscar','Daniel','Ivan','Fabian')")
    )
