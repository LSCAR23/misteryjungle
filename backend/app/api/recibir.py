"""Recepción de vehículos (PLAN §2 regla 3, §3 GET/POST /api/recibir)."""
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbSession
from app.enums import UBICACIONES_REALES, EstadoPlaca, EstadoRenta, Ubicacion
from app.models import Placa, Renta, Vehiculo
from app.salidas import PlacaOut, RentaOut, nombre_vehiculo, placa_out, renta_out
from app.services.vencimientos import dep_sincronizar
from app.timeutil import now_utc, rango_dia_cr

router = APIRouter(tags=["recibir"])


class PlacaSinUbicacionOut(PlacaOut):
    vehiculo: str


class RecibirOut(BaseModel):
    vencidas: list[RentaOut]
    hoy: list[RentaOut]
    sin_ubicacion: list[PlacaSinUbicacionOut]


class RecibirIn(BaseModel):
    renta_ids: list[UUID] = Field(default_factory=list)
    placa_ids: list[UUID] = Field(default_factory=list)
    ubicacion: Ubicacion


class RecibirResultado(BaseModel):
    rentas_finalizadas: int
    placas_actualizadas: int


_RENTA_LOAD = (
    selectinload(Renta.placa),
    selectinload(Renta.vehiculo),
    selectinload(Renta.usuario),
)


@router.get("/recibir", response_model=RecibirOut, dependencies=[Depends(dep_sincronizar)])
def listar(_: CurrentUser, db: DbSession):
    inicio, fin = rango_dia_cr(now_utc())
    vencidas = db.scalars(
        sa.select(Renta)
        .options(*_RENTA_LOAD)
        .where(Renta.estado == EstadoRenta.VENCIDA_SIN_RECIBIR)
        .order_by(Renta.fin_programado, Renta.id)
    ).all()
    hoy = db.scalars(
        sa.select(Renta)
        .options(*_RENTA_LOAD)
        .where(
            Renta.estado == EstadoRenta.ACTIVA,
            Renta.fin_programado >= inicio,
            Renta.fin_programado < fin,
        )
        .order_by(Renta.fin_programado, Renta.id)
    ).all()
    pendiente = sa.exists().where(
        Renta.placa_id == Placa.id, Renta.estado == EstadoRenta.VENCIDA_SIN_RECIBIR
    )
    placas = db.scalars(
        sa.select(Placa)
        .join(Vehiculo, Vehiculo.id == Placa.vehiculo_id)
        .options(selectinload(Placa.vehiculo))
        .where(
            Placa.ubicacion_actual == Ubicacion.NO_ACTUALIZADA,
            Placa.estado != EstadoPlaca.RENTADA,  # las rentadas se ubican al recibirlas
            ~pendiente,
        )
        .order_by(Vehiculo.marca, Vehiculo.modelo, Placa.placa, Placa.id)
    ).all()
    return RecibirOut(
        vencidas=[renta_out(r) for r in vencidas],
        hoy=[renta_out(r) for r in hoy],
        sin_ubicacion=[
            PlacaSinUbicacionOut(**placa_out(p).model_dump(), vehiculo=nombre_vehiculo(p.vehiculo))
            for p in placas
        ],
    )


def _recibir(data: RecibirIn, usuario, db) -> RecibirResultado:
    now = now_utc()
    cambiadas: set[UUID] = set()
    finalizadas = 0

    for renta_id in dict.fromkeys(data.renta_ids):
        r = db.scalar(sa.select(Renta).where(Renta.id == renta_id).with_for_update())
        if r is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Renta no encontrada")
        if r.estado not in (EstadoRenta.ACTIVA, EstadoRenta.VENCIDA_SIN_RECIBIR):
            raise HTTPException(status.HTTP_409_CONFLICT, "La renta ya fue recibida")
        placa = db.scalar(sa.select(Placa).where(Placa.id == r.placa_id).with_for_update())

        if r.estado == EstadoRenta.ACTIVA:
            r.fin_real = now  # devolución anticipada; el monto no cambia
        # ¿La placa la tiene otra renta activa (más nueva)? Entonces no se toca.
        otra = db.scalar(
            sa.select(Renta.id)
            .where(Renta.placa_id == r.placa_id, Renta.estado == EstadoRenta.ACTIVA, Renta.id != r.id)
            .limit(1)
        )
        if otra is None and not (
            r.estado == EstadoRenta.VENCIDA_SIN_RECIBIR and placa.estado == EstadoPlaca.RENTADA
        ):
            if placa.ubicacion_actual != data.ubicacion:
                cambiadas.add(placa.id)
            placa.ubicacion_actual = data.ubicacion
            if placa.estado == EstadoPlaca.RENTADA:
                placa.estado = EstadoPlaca.DISPONIBLE
                placa.fecha_hora_finalizacion = None
                cambiadas.add(placa.id)

        r.estado = EstadoRenta.FINALIZADA
        r.ubicacion_recibida = data.ubicacion
        r.recibida_por = usuario.id
        r.recibida_en = now
        finalizadas += 1
        db.flush()

    for placa_id in dict.fromkeys(data.placa_ids):
        placa = db.scalar(sa.select(Placa).where(Placa.id == placa_id).with_for_update())
        if placa is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Placa no encontrada")
        if placa.estado == EstadoPlaca.RENTADA:
            raise HTTPException(status.HTTP_409_CONFLICT, "La placa está rentada")
        if placa.ubicacion_actual != data.ubicacion:
            cambiadas.add(placa.id)
        placa.ubicacion_actual = data.ubicacion
        db.flush()

    return RecibirResultado(rentas_finalizadas=finalizadas, placas_actualizadas=len(cambiadas))


@router.post("/recibir", response_model=RecibirResultado, dependencies=[Depends(dep_sincronizar)])
def recibir(data: RecibirIn, usuario: CurrentUser, db: DbSession):
    if not data.renta_ids and not data.placa_ids:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Elige al menos una renta o placa")
    if data.ubicacion not in UBICACIONES_REALES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Elige una ubicación válida")
    try:
        resultado = _recibir(data, usuario, db)
    except HTTPException:
        db.rollback()
        raise
    db.commit()
    return resultado
