from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbSession
from app.enums import Categoria, EstadoPlaca, Ubicacion
from app.models import Placa, Vehiculo
from app.salidas import VehiculoOut, vehiculo_out
from app.services.vencimientos import dep_sincronizar

router = APIRouter(tags=["disponibilidad"], dependencies=[Depends(dep_sincronizar)])


class CategoriaResumenOut(BaseModel):
    categoria: Categoria
    disponibles: int
    total: int


class UbicacionConteo(BaseModel):
    ubicacion: Ubicacion
    disponibles: int


class VehiculoDisponibilidadOut(VehiculoOut):
    disponibles: int
    por_ubicacion: list[UbicacionConteo]


@router.get("/disponibilidad/categorias", response_model=list[CategoriaResumenOut])
def categorias(_: CurrentUser, db: DbSession):
    disp = func.count(Placa.id).filter(Placa.estado == EstadoPlaca.DISPONIBLE)
    filas = db.execute(
        select(Vehiculo.categoria, disp, func.count(Placa.id))
        .select_from(Vehiculo)
        .join(Placa, Placa.vehiculo_id == Vehiculo.id)
        .group_by(Vehiculo.categoria)
    ).all()
    por_cat = {f[0]: (f[1], f[2]) for f in filas}
    return [
        CategoriaResumenOut(
            categoria=c, disponibles=por_cat.get(c, (0, 0))[0], total=por_cat.get(c, (0, 0))[1]
        )
        for c in Categoria
    ]


@router.get("/disponibilidad", response_model=list[VehiculoDisponibilidadOut])
def por_categoria(categoria: Categoria, _: CurrentUser, db: DbSession):
    vehiculos = db.scalars(
        select(Vehiculo)
        .where(Vehiculo.categoria == categoria)
        .options(selectinload(Vehiculo.precios), selectinload(Vehiculo.placas))
    ).all()
    filas = db.execute(
        select(Placa.vehiculo_id, Placa.ubicacion_actual, func.count(Placa.id))
        .join(Vehiculo, Vehiculo.id == Placa.vehiculo_id)
        .where(Vehiculo.categoria == categoria, Placa.estado == EstadoPlaca.DISPONIBLE)
        .group_by(Placa.vehiculo_id, Placa.ubicacion_actual)
    ).all()
    ubic: dict[UUID, list[UbicacionConteo]] = defaultdict(list)
    for vid, u, n in filas:
        ubic[vid].append(UbicacionConteo(ubicacion=u, disponibles=n))

    salida = []
    for v in vehiculos:
        lista = sorted(ubic.get(v.id, []), key=lambda x: (-x.disponibles, x.ubicacion.value))
        salida.append(
            VehiculoDisponibilidadOut(
                **vehiculo_out(v).model_dump(),
                disponibles=sum(x.disponibles for x in lista),
                por_ubicacion=lista,
            )
        )
    salida.sort(key=lambda x: (-x.disponibles, x.marca.lower(), x.modelo.lower()))
    return salida
