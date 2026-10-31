from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import AwareDatetime, BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.deps import CurrentUser, DbSession
from app.enums import EstadoPlaca, EstadoRenta
from app.models import Placa, Renta
from app.salidas import (
    CotizacionItem,
    CotizacionOut,
    RentaOut,
    nombre_vehiculo,
    precios_dict,
    renta_out,
)
from app.services.pricing import cotizar
from app.services.vencimientos import dep_sincronizar
from app.timeutil import now_utc

router = APIRouter(tags=["rentas"], dependencies=[Depends(dep_sincronizar)])

MIN_RENTA = timedelta(minutes=15)
MAX_RENTA = timedelta(days=90)


class RentaCreate(BaseModel):
    placa_ids: list[UUID] = Field(min_length=1)
    fin: AwareDatetime


class ExtenderIn(BaseModel):
    fin: AwareDatetime


def _unprocessable(msg: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, msg)


def _validar_fin(fin: datetime, inicio: datetime, base: datetime) -> None:
    """fin > base + 15 min y fin <= inicio + 90 días."""
    if fin <= base + MIN_RENTA:
        raise _unprocessable("La fecha de fin debe ser al menos 15 minutos después de ahora")
    if fin > inicio + MAX_RENTA:
        raise _unprocessable("La fecha de fin no puede superar los 90 días")


def _validar_ids(ids: list[UUID]) -> None:
    if len(set(ids)) != len(ids):
        raise _unprocessable("Hay placas repetidas en la solicitud")


def _cotizar(precios, inicio, fin) -> tuple[Decimal, str]:
    try:
        return cotizar(precios, inicio, fin)
    except ValueError as e:
        raise _unprocessable(str(e))


@router.post("/rentas/cotizar", response_model=CotizacionOut)
def cotizar_rentas(data: RentaCreate, _: CurrentUser, db: DbSession):
    _validar_ids(data.placa_ids)
    inicio = now_utc()
    _validar_fin(data.fin, inicio, inicio)
    placas = db.scalars(
        select(Placa).where(Placa.id.in_(data.placa_ids)).options(joinedload(Placa.vehiculo))
    ).all()
    por_id = {p.id: p for p in placas}
    if len(por_id) != len(data.placa_ids):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Placa no encontrada")
    items = []
    total = Decimal(0)
    for pid in data.placa_ids:
        p = por_id[pid]
        monto, desglose = _cotizar(precios_dict(p.vehiculo), inicio, data.fin)
        total += monto
        items.append(
            CotizacionItem(
                placa_id=p.id,
                vehiculo=nombre_vehiculo(p.vehiculo),
                placa=p.placa,
                monto=float(monto),
                desglose=desglose,
            )
        )
    return CotizacionOut(inicio=inicio, fin=data.fin, items=items, total=float(total))


@router.post("/rentas", response_model=list[RentaOut], status_code=status.HTTP_201_CREATED)
def crear_rentas(data: RentaCreate, usuario: CurrentUser, db: DbSession):
    _validar_ids(data.placa_ids)
    inicio = now_utc()
    _validar_fin(data.fin, inicio, inicio)
    placas = db.scalars(
        select(Placa).where(Placa.id.in_(data.placa_ids)).order_by(Placa.id).with_for_update()
    ).all()
    if len(placas) != len(data.placa_ids):
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Placa no encontrada")
    if any(p.estado != EstadoPlaca.DISPONIBLE for p in placas):
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Una o más placas ya no están disponibles")

    rentas = []
    try:
        for p in placas:
            monto, desglose = _cotizar(precios_dict(p.vehiculo), inicio, data.fin)
            rentas.append(
                Renta(
                    placa_id=p.id,
                    vehiculo_id=p.vehiculo_id,
                    usuario_id=usuario.id,
                    inicio=inicio,
                    fin_programado=data.fin,
                    monto=monto,
                    desglose=desglose,
                    estado=EstadoRenta.ACTIVA,
                )
            )
            p.estado = EstadoPlaca.RENTADA
            p.fecha_hora_finalizacion = data.fin
    except HTTPException:
        db.rollback()
        raise
    db.add_all(rentas)
    db.commit()
    for r in rentas:
        db.refresh(r)
    orden = {pid: i for i, pid in enumerate(data.placa_ids)}
    rentas.sort(key=lambda r: orden[r.placa_id])
    return [renta_out(r) for r in rentas]


@router.get("/rentas/activas", response_model=list[RentaOut])
def activas(_: CurrentUser, db: DbSession):
    rentas = db.scalars(
        select(Renta)
        .where(Renta.estado == EstadoRenta.ACTIVA)
        .options(joinedload(Renta.placa), joinedload(Renta.vehiculo), joinedload(Renta.usuario))
        .order_by(Renta.fin_programado, Renta.id)
    ).all()
    return [renta_out(r) for r in rentas]


def _renta_extensible(db, renta_id: UUID, lock: bool = False) -> Renta:
    q = select(Renta).where(Renta.id == renta_id)
    if lock:
        q = q.with_for_update()
    renta = db.scalars(q).first()
    if renta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Renta no encontrada")
    if renta.estado == EstadoRenta.FINALIZADA:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esta renta ya fue cerrada")
    return renta


@router.post("/rentas/{renta_id}/extender/cotizar", response_model=CotizacionOut)
def extender_cotizar(renta_id: UUID, data: ExtenderIn, _: CurrentUser, db: DbSession):
    renta = _renta_extensible(db, renta_id)
    inicio = renta.fin_programado
    _validar_fin(data.fin, inicio, max(now_utc(), inicio))
    monto, desglose = _cotizar(precios_dict(renta.vehiculo), inicio, data.fin)
    item = CotizacionItem(
        placa_id=renta.placa_id,
        vehiculo=nombre_vehiculo(renta.vehiculo),
        placa=renta.placa.placa,
        monto=float(monto),
        desglose=desglose,
    )
    return CotizacionOut(inicio=inicio, fin=data.fin, items=[item], total=float(monto))


@router.post(
    "/rentas/{renta_id}/extender", response_model=RentaOut, status_code=status.HTTP_201_CREATED
)
def extender(renta_id: UUID, data: ExtenderIn, usuario: CurrentUser, db: DbSession):
    renta = _renta_extensible(db, renta_id, lock=True)
    placa = db.scalars(select(Placa).where(Placa.id == renta.placa_id).with_for_update()).one()
    now = now_utc()
    inicio = renta.fin_programado
    try:
        _validar_fin(data.fin, inicio, max(now, inicio))
    except HTTPException:
        db.rollback()
        raise

    if renta.estado == EstadoRenta.ACTIVA:
        ok = (
            placa.estado == EstadoPlaca.RENTADA
            and placa.fecha_hora_finalizacion == renta.fin_programado
        )
    else:
        ok = placa.estado == EstadoPlaca.DISPONIBLE
    if not ok:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "La placa ya no está disponible para extender")

    try:
        monto, desglose = _cotizar(precios_dict(renta.vehiculo), inicio, data.fin)
    except HTTPException:
        db.rollback()
        raise

    renta.estado = EstadoRenta.FINALIZADA
    renta.fin_real = renta.fin_programado
    renta.recibida_por = usuario.id
    renta.recibida_en = now
    renta.ubicacion_recibida = None
    nueva = Renta(
        placa_id=placa.id,
        vehiculo_id=renta.vehiculo_id,
        usuario_id=usuario.id,
        inicio=inicio,
        fin_programado=data.fin,
        monto=monto,
        desglose=desglose,
        estado=EstadoRenta.ACTIVA,
    )
    placa.estado = EstadoPlaca.RENTADA
    placa.fecha_hora_finalizacion = data.fin
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return renta_out(nueva)
