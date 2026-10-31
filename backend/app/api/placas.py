import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.deps import AdminUser, DbSession
from app.enums import EstadoPlaca, Ubicacion
from app.models import Placa
from app.salidas import PlacaOut, placa_out
from app.services.vencimientos import dep_sincronizar

router = APIRouter(tags=["placas"])


class PlacaPatch(BaseModel):
    placa: str | None = Field(default=None, max_length=20)
    ubicacion_actual: Ubicacion | None = None

    @field_validator("placa")
    @classmethod
    def _placa(cls, v):
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("La placa no puede estar vacía")
        return v.upper()

    @field_validator("ubicacion_actual")
    @classmethod
    def _ubi(cls, v):
        if v == Ubicacion.NO_ACTUALIZADA:
            raise ValueError("Ubicación no válida")
        return v


class EstadoIn(BaseModel):
    placa_ids: list[uuid.UUID] = Field(min_length=1, max_length=200)
    accion: Literal["fuera_servicio", "habilitar"]


@router.patch(
    "/placas/{placa_id}",
    response_model=PlacaOut,
    dependencies=[Depends(dep_sincronizar)],
)
def editar(placa_id: uuid.UUID, data: PlacaPatch, _: AdminUser, db: DbSession):
    p = db.scalar(select(Placa).where(Placa.id == placa_id).with_for_update())
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Placa no encontrada")
    if data.ubicacion_actual is not None and data.ubicacion_actual != p.ubicacion_actual:
        if p.estado == EstadoPlaca.RENTADA:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "No se puede cambiar la ubicación de una placa rentada"
            )
        p.ubicacion_actual = data.ubicacion_actual
    if data.placa is not None and data.placa != p.placa.upper():
        if data.placa != "NUEVA":
            existe = db.scalar(
                select(Placa.placa).where(func.upper(Placa.placa) == data.placa, Placa.id != p.id)
            )
            if existe:
                raise HTTPException(status.HTTP_409_CONFLICT, f"La placa {data.placa} ya existe")
        p.placa = data.placa
    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, f"La placa {data.placa} ya existe")
    db.commit()
    db.refresh(p)
    return placa_out(p)


@router.post(
    "/placas/estado",
    response_model=list[PlacaOut],
    dependencies=[Depends(dep_sincronizar)],
)
def cambiar_estado(data: EstadoIn, _: AdminUser, db: DbSession):
    ids = list(dict.fromkeys(data.placa_ids))
    placas = db.scalars(
        select(Placa).where(Placa.id.in_(ids)).order_by(Placa.id).with_for_update()
    ).all()
    por_id = {p.id: p for p in placas}
    if len(por_id) != len(ids):
        db.rollback()
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Placa no encontrada")

    if data.accion == "fuera_servicio":
        requerido, nuevo = EstadoPlaca.DISPONIBLE, EstadoPlaca.FUERA_DE_SERVICIO
        msg = "Solo se pueden poner fuera de servicio placas Disponibles"
    else:
        requerido, nuevo = EstadoPlaca.FUERA_DE_SERVICIO, EstadoPlaca.DISPONIBLE
        msg = "Solo se pueden habilitar placas Fuera de Servicio"
    if any(p.estado != requerido for p in placas):
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, msg)

    for p in placas:
        p.estado = nuevo
    db.commit()
    return [placa_out(por_id[i]) for i in ids]
