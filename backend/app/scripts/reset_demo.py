"""Reinicia los datos de demo: python -m app.scripts.reset_demo

También disponible para admins en POST /api/demo/reset (Render free no tiene consola).
"""
from datetime import datetime, timezone

import sqlalchemy as sa

from app.db import engine
from app.seed.catalogo import CATALOGO
from app.seed.mock_data import generar

USUARIOS_SEED = ("oscar", "daniel", "ivan", "fabian")

ETIQUETAS = {
    "placas_con_numero": "Placas con número real",
    "rentas_finalizadas": "Rentas históricas finalizadas",
    "rentadas": "Placas rentadas ahora",
    "rentadas_hoy": "  de ellas, terminan hoy",
    "vencidas_sin_recibir": "Rentas vencidas sin recibir",
    "fuera_de_servicio": "Placas fuera de servicio",
    "disponibles": "Placas disponibles",
}


def reiniciar(conn: sa.Connection, now: datetime) -> dict:
    """Borra rentas y lo creado durante pruebas (vehículos y usuarios extra) y regenera el mock."""
    slugs = [v["slug"] for v in CATALOGO]
    conn.execute(sa.text("DELETE FROM rentas"))
    # Vehículos agregados a mano (precios y placas se borran en cascada)
    conn.execute(
        sa.text("DELETE FROM vehiculos WHERE slug NOT IN :slugs").bindparams(
            sa.bindparam("slugs", expanding=True)
        ),
        {"slugs": slugs},
    )
    conn.execute(
        sa.text("DELETE FROM usuarios WHERE lower(username) NOT IN :u").bindparams(
            sa.bindparam("u", expanding=True)
        ),
        {"u": list(USUARIOS_SEED)},
    )
    conn.execute(
        sa.text(
            "UPDATE placas SET placa = 'NUEVA', estado = 'Disponible', "
            "ubicacion_actual = 'Puerto Viejo', fecha_hora_finalizacion = NULL"
        )
    )
    return generar(conn, now)


def main() -> None:
    with engine.begin() as conn:
        resumen = reiniciar(conn, datetime.now(timezone.utc))
    print("Datos de demo reiniciados:")
    for k, v in resumen.items():
        print(f"  {ETIQUETAS.get(k, k)}: {v}")


if __name__ == "__main__":
    main()
