"""Reinicia los datos de demo: python -m app.scripts.reset_demo"""
from datetime import datetime, timezone

import sqlalchemy as sa

from app.db import engine
from app.seed.mock_data import generar

ETIQUETAS = {
    "placas_con_numero": "Placas con número real",
    "rentas_finalizadas": "Rentas históricas finalizadas",
    "rentadas": "Placas rentadas ahora",
    "rentadas_hoy": "  de ellas, terminan hoy",
    "vencidas_sin_recibir": "Rentas vencidas sin recibir",
    "fuera_de_servicio": "Placas fuera de servicio",
    "disponibles": "Placas disponibles",
}


def main() -> None:
    now = datetime.now(timezone.utc)
    with engine.begin() as conn:
        conn.execute(sa.text("DELETE FROM rentas"))
        conn.execute(
            sa.text(
                "UPDATE placas SET placa = 'NUEVA', estado = 'Disponible', "
                "ubicacion_actual = 'Puerto Viejo', fecha_hora_finalizacion = NULL"
            )
        )
        resumen = generar(conn, now)
    print("Datos de demo reiniciados:")
    for k, v in resumen.items():
        print(f"  {ETIQUETAS.get(k, k)}: {v}")


if __name__ == "__main__":
    main()
