"""datos de demostración (rentas y estado actual de la flota)

Revision ID: 0004
Revises: 0003
"""
import os
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if os.environ.get("SEED_MOCK_DATA", "true").lower() == "false":
        return
    from app.seed.mock_data import generar

    generar(op.get_bind(), datetime.now(timezone.utc))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM rentas"))
    conn.execute(
        sa.text(
            "UPDATE placas SET placa = 'NUEVA', estado = 'Disponible', "
            "ubicacion_actual = 'Puerto Viejo', fecha_hora_finalizacion = NULL"
        )
    )
