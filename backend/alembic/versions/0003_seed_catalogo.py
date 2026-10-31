"""seed del catálogo de vehículos, precios y placas (PLAN §5)

Revision ID: 0003
Revises: 0002
"""
import uuid

import sqlalchemy as sa
from alembic import op

from app.seed.catalogo import CATALOGO, UBICACIONES_INICIALES

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    contador = 0  # round-robin global entre todos los vehículos

    for v in CATALOGO:
        vehiculo_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                "INSERT INTO vehiculos (id, marca, modelo, slug, imagen, cilindrada, categoria) "
                "VALUES (CAST(:id AS uuid), :marca, :modelo, :slug, :imagen, :cilindrada, :categoria)"
            ),
            {
                "id": vehiculo_id,
                "marca": v["marca"],
                "modelo": v["modelo"],
                "slug": v["slug"],
                "imagen": v["imagen"],
                "cilindrada": v["cilindrada"],
                "categoria": v["categoria"],
            },
        )

        for tarifa, monto in v["precios"].items():
            conn.execute(
                sa.text(
                    "INSERT INTO precios (id, vehiculo_id, tarifa, monto) "
                    "VALUES (CAST(:id AS uuid), CAST(:vehiculo_id AS uuid), :tarifa, :monto)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "vehiculo_id": vehiculo_id,
                    "tarifa": tarifa,
                    "monto": monto,
                },
            )

        for _ in range(v["unidades"]):
            ubicacion = UBICACIONES_INICIALES[contador % len(UBICACIONES_INICIALES)]
            contador += 1
            conn.execute(
                sa.text(
                    "INSERT INTO placas (id, placa, vehiculo_id, estado, ubicacion_actual) "
                    "VALUES (CAST(:id AS uuid), 'NUEVA', CAST(:vehiculo_id AS uuid), "
                    "'Disponible', :ubicacion)"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "vehiculo_id": vehiculo_id,
                    "ubicacion": ubicacion,
                },
            )


def downgrade() -> None:
    conn = op.get_bind()
    slugs = [v["slug"] for v in CATALOGO]
    subq = "(SELECT id FROM vehiculos WHERE slug IN :slugs)"

    # rentas referencian placas (sin ON DELETE CASCADE): borrarlas primero
    conn.execute(
        sa.text(f"DELETE FROM rentas WHERE vehiculo_id IN {subq}").bindparams(
            sa.bindparam("slugs", expanding=True)
        ),
        {"slugs": slugs},
    )
    for tabla in ("placas", "precios"):
        conn.execute(
            sa.text(f"DELETE FROM {tabla} WHERE vehiculo_id IN {subq}").bindparams(
                sa.bindparam("slugs", expanding=True)
            ),
            {"slugs": slugs},
        )
    conn.execute(
        sa.text("DELETE FROM vehiculos WHERE slug IN :slugs").bindparams(
            sa.bindparam("slugs", expanding=True)
        ),
        {"slugs": slugs},
    )
