"""Vencimiento automático de rentas (PLAN §1 y §2 regla 2)."""
from datetime import datetime

import sqlalchemy as sa
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import EstadoPlaca, EstadoRenta, Ubicacion
from app.models import Placa, Renta
from app.timeutil import now_utc


def sincronizar_vencidas(db: Session, now: datetime | None = None) -> int:
    """Marca como vencidas las rentas activas cuyo fin ya pasó y libera sus placas.

    Devuelve la cantidad de rentas actualizadas. Idempotente.
    """
    now = now or now_utc()
    rentas = db.execute(
        sa.select(Renta.id, Renta.placa_id, Renta.fin_programado).where(
            Renta.estado == EstadoRenta.ACTIVA, Renta.fin_programado <= now
        )
    ).all()
    if not rentas:
        db.commit()
        return 0

    placa_ids = list({r.placa_id for r in rentas})
    db.execute(
        sa.update(Placa)
        .where(
            Placa.id.in_(placa_ids),
            Placa.estado == EstadoPlaca.RENTADA,
            Placa.fecha_hora_finalizacion <= now,
        )
        .values(
            estado=EstadoPlaca.DISPONIBLE,
            fecha_hora_finalizacion=None,
            ubicacion_actual=Ubicacion.NO_ACTUALIZADA,
        )
        .execution_options(synchronize_session=False)
    )
    db.execute(
        sa.update(Renta)
        .where(Renta.id.in_([r.id for r in rentas]))
        .values(estado=EstadoRenta.VENCIDA_SIN_RECIBIR, fin_real=Renta.fin_programado)
        .execution_options(synchronize_session=False)
    )
    db.commit()
    return len(rentas)


def dep_sincronizar(db: Session = Depends(get_db)) -> None:
    sincronizar_vencidas(db)
