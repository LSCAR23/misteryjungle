"""esquema inicial

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

CATEGORIAS = ["Scooter", "Moto", "ATV", "UTV", "Camion"]
UBICACIONES = [
    "Playa Chiquita", "Puerto Viejo", "Playa Negra", "B.Azul", "Taller Nico",
    "Ubicación no actualizada",
]
ESTADOS_PLACA = ["Rentada", "Disponible", "Fuera de Servicio"]
ROLES = ["admin", "empleado"]
TARIFAS = ["5H", "DIA", "24H", "2D", "3D", "1S", "10D", "MES"]
ESTADOS_RENTA = ["activa", "vencida_sin_recibir", "finalizada"]


def _in(col: str, values: list) -> str:
    lista = ", ".join("'%s'" % v for v in values)
    return "%s IN (%s)" % (col, lista)


def _uuid_pk():
    return sa.Column(
        "id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()"), nullable=False
    )


def _created_at():
    return sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )


def upgrade() -> None:
    op.create_table(
        "usuarios",
        _uuid_pk(),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("password_hash", sa.String(100), nullable=False),
        sa.Column("rol", sa.String(40), nullable=False),
        sa.Column("activo", sa.Boolean(), server_default=sa.true(), nullable=False),
        _created_at(),
        sa.CheckConstraint(_in("rol", ROLES), name="ck_usuarios_rol"),
    )
    op.create_index(
        "uq_usuarios_username_lower", "usuarios", [sa.text("lower(username)")], unique=True
    )

    op.create_table(
        "vehiculos",
        _uuid_pk(),
        sa.Column("marca", sa.String(50), nullable=False),
        sa.Column("modelo", sa.String(80), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False),
        sa.Column("imagen", sa.String(255), nullable=True),
        sa.Column("cilindrada", sa.Integer(), nullable=False),
        sa.Column("categoria", sa.String(40), nullable=False),
        _created_at(),
        sa.UniqueConstraint("slug"),
        sa.CheckConstraint("cilindrada > 0", name="ck_vehiculos_cilindrada"),
        sa.CheckConstraint(_in("categoria", CATEGORIAS), name="ck_vehiculos_categoria"),
    )

    op.create_table(
        "precios",
        _uuid_pk(),
        sa.Column("vehiculo_id", sa.Uuid(), nullable=False),
        sa.Column("tarifa", sa.String(40), nullable=False),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(["vehiculo_id"], ["vehiculos.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("vehiculo_id", "tarifa", name="uq_precios_vehiculo_tarifa"),
        sa.CheckConstraint("monto > 0", name="ck_precios_monto"),
        sa.CheckConstraint(_in("tarifa", TARIFAS), name="ck_precios_tarifa"),
    )

    op.create_table(
        "placas",
        _uuid_pk(),
        sa.Column("placa", sa.String(20), server_default="NUEVA", nullable=False),
        sa.Column("vehiculo_id", sa.Uuid(), nullable=False),
        sa.Column("estado", sa.String(40), server_default="Disponible", nullable=False),
        sa.Column("ubicacion_actual", sa.String(40), server_default="Taller Nico", nullable=False),
        sa.Column("fecha_hora_finalizacion", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(["vehiculo_id"], ["vehiculos.id"], ondelete="CASCADE"),
        sa.CheckConstraint(_in("estado", ESTADOS_PLACA), name="ck_placas_estado"),
        sa.CheckConstraint(_in("ubicacion_actual", UBICACIONES), name="ck_placas_ubicacion_actual"),
        sa.CheckConstraint(
            "((estado = 'Rentada') = (fecha_hora_finalizacion IS NOT NULL))",
            name="ck_placas_estado_fecha",
        ),
    )
    op.create_index(
        "uq_placas_placa",
        "placas",
        [sa.text("upper(placa)")],
        unique=True,
        postgresql_where=sa.text("upper(placa) <> 'NUEVA'"),
    )
    op.create_index("ix_placas_vehiculo_id", "placas", ["vehiculo_id"])
    op.create_index("ix_placas_estado", "placas", ["estado"])

    op.create_table(
        "rentas",
        _uuid_pk(),
        sa.Column("placa_id", sa.Uuid(), nullable=False),
        sa.Column("vehiculo_id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("inicio", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin_programado", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin_real", sa.DateTime(timezone=True), nullable=True),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.Column("desglose", sa.String(120), nullable=False),
        sa.Column("estado", sa.String(40), server_default="activa", nullable=False),
        sa.Column("ubicacion_recibida", sa.String(40), nullable=True),
        sa.Column("recibida_por", sa.Uuid(), nullable=True),
        sa.Column("recibida_en", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
        sa.ForeignKeyConstraint(["placa_id"], ["placas.id"]),
        sa.ForeignKeyConstraint(["vehiculo_id"], ["vehiculos.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["recibida_por"], ["usuarios.id"]),
        sa.CheckConstraint(_in("estado", ESTADOS_RENTA), name="ck_rentas_estado"),
        sa.CheckConstraint(
            _in("ubicacion_recibida", UBICACIONES), name="ck_rentas_ubicacion_recibida"
        ),
    )
    op.create_index("ix_rentas_estado", "rentas", ["estado"])
    op.create_index("ix_rentas_fin_programado", "rentas", ["fin_programado"])
    op.create_index("ix_rentas_inicio", "rentas", ["inicio"])


def downgrade() -> None:
    op.drop_table("rentas")
    op.drop_table("placas")
    op.drop_table("precios")
    op.drop_table("vehiculos")
    op.drop_table("usuarios")
