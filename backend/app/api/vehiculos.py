import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator, model_validator
from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.deps import AdminUser, CurrentUser, DbSession
from app.enums import UBICACIONES_REALES, Categoria, Tarifa, Ubicacion
from app.models import Placa, Precio, Vehiculo
from app.salidas import (
    PlacaOut,
    VehiculoDetalleOut,
    VehiculoOut,
    placa_out,
    vehiculo_detalle_out,
    vehiculo_out,
)
from app.services.vencimientos import dep_sincronizar

router = APIRouter(tags=["vehiculos"])

_NO_ENCONTRADO = "Vehículo no encontrado"


def normalizar_placa(valor: str | None) -> str:
    texto = (valor or "").strip().upper()
    return texto or "NUEVA"


def _ubicacion_real(v: Ubicacion) -> Ubicacion:
    if v not in UBICACIONES_REALES:
        raise ValueError("Ubicación no válida")
    return v


class PrecioIn(BaseModel):
    tarifa: Tarifa
    monto: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class PlacaCreate(BaseModel):
    placa: str | None = Field(default=None, max_length=20)
    ubicacion_actual: Ubicacion

    @field_validator("placa")
    @classmethod
    def _placa(cls, v):
        return normalizar_placa(v)

    @field_validator("ubicacion_actual")
    @classmethod
    def _ubi(cls, v):
        return _ubicacion_real(v)

    @model_validator(mode="before")
    @classmethod
    def _placa_ausente(cls, data):
        # Fuerza a pasar por el validador de placa aunque no venga el campo.
        if isinstance(data, dict) and data.get("placa") is None:
            data = {**data, "placa": ""}
        return data


class VehiculoCreate(BaseModel):
    marca: str = Field(min_length=1, max_length=50)
    modelo: str = Field(min_length=1, max_length=80)
    cilindrada: int = Field(gt=0)
    categoria: Categoria
    imagen: str | None = Field(default=None, max_length=255)
    precios: list[PrecioIn] = Field(min_length=1)
    placas: list[PlacaCreate] = Field(min_length=1, max_length=50)

    @field_validator("marca", "modelo")
    @classmethod
    def _strip(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("No puede estar vacío")
        return v

    @field_validator("precios")
    @classmethod
    def _tarifas_unicas(cls, v):
        tarifas = [p.tarifa for p in v]
        if len(set(tarifas)) != len(tarifas):
            raise ValueError("Tarifas repetidas")
        return v


def duplicadas_en_bd(db, placas: list[str]) -> str | None:
    """Primera placa real (no NUEVA) que ya existe en la BD, o None."""
    reales = {p for p in placas if p != "NUEVA"}
    if not reales:
        return None
    return db.scalar(select(Placa.placa).where(func.upper(Placa.placa).in_(reales)).limit(1))


def _generar_slug(db, marca: str, modelo: str) -> str:
    base = (slugify(f"{marca}-{modelo}") or "vehiculo")[:90]
    slug, n = base, 2
    while db.scalar(select(Vehiculo.id).where(Vehiculo.slug == slug)):
        slug = f"{base}-{n}"
        n += 1
    return slug


def _cargar(db, vehiculo_id) -> Vehiculo | None:
    return db.scalar(
        select(Vehiculo)
        .where(Vehiculo.id == vehiculo_id)
        .options(selectinload(Vehiculo.precios), selectinload(Vehiculo.placas))
        .execution_options(populate_existing=True)
    )


@router.get(
    "/vehiculos",
    response_model=list[VehiculoOut],
    dependencies=[Depends(dep_sincronizar)],
)
def listar(
    _: CurrentUser,
    db: DbSession,
    categoria: Annotated[Categoria | None, Query()] = None,
):
    stmt = select(Vehiculo).options(
        selectinload(Vehiculo.precios), selectinload(Vehiculo.placas)
    )
    if categoria is not None:
        stmt = stmt.where(Vehiculo.categoria == categoria)
    orden = {c: i for i, c in enumerate(Categoria)}
    vehiculos = sorted(
        db.scalars(stmt).all(),
        key=lambda v: (orden[v.categoria], v.marca.lower(), v.modelo.lower()),
    )
    return [vehiculo_out(v) for v in vehiculos]


@router.get(
    "/vehiculos/{vehiculo_id}",
    response_model=VehiculoDetalleOut,
    dependencies=[Depends(dep_sincronizar)],
)
def detalle(vehiculo_id: uuid.UUID, _: CurrentUser, db: DbSession):
    v = _cargar(db, vehiculo_id)
    if v is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NO_ENCONTRADO)
    return vehiculo_detalle_out(v)


@router.post(
    "/vehiculos",
    response_model=VehiculoDetalleOut,
    status_code=status.HTTP_201_CREATED,
)
def crear(data: VehiculoCreate, _: AdminUser, db: DbSession):
    placas = [p.placa for p in data.placas]
    reales = [p for p in placas if p != "NUEVA"]
    if len(set(reales)) != len(reales):
        dup = next(p for p in reales if reales.count(p) > 1)
        raise HTTPException(status.HTTP_409_CONFLICT, f"La placa {dup} ya existe")
    dup = duplicadas_en_bd(db, placas)
    if dup:
        raise HTTPException(status.HTTP_409_CONFLICT, f"La placa {dup} ya existe")

    slug = _generar_slug(db, data.marca, data.modelo)
    imagen = (data.imagen or "").strip() or f"/vehiculos/{slug}.png"
    v = Vehiculo(
        marca=data.marca,
        modelo=data.modelo,
        slug=slug,
        imagen=imagen,
        cilindrada=data.cilindrada,
        categoria=data.categoria,
        precios=[Precio(tarifa=p.tarifa, monto=p.monto) for p in data.precios],
        placas=[Placa(placa=p.placa, ubicacion_actual=p.ubicacion_actual) for p in data.placas],
    )
    db.add(v)
    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "La placa o el vehículo ya existe")
    db.commit()
    return vehiculo_detalle_out(_cargar(db, v.id))


@router.post(
    "/vehiculos/{vehiculo_id}/placas",
    response_model=PlacaOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(dep_sincronizar)],
)
def agregar_placa(vehiculo_id: uuid.UUID, data: PlacaCreate, _: AdminUser, db: DbSession):
    if db.get(Vehiculo, vehiculo_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, _NO_ENCONTRADO)
    dup = duplicadas_en_bd(db, [data.placa])
    if dup:
        raise HTTPException(status.HTTP_409_CONFLICT, f"La placa {dup} ya existe")
    p = Placa(vehiculo_id=vehiculo_id, placa=data.placa, ubicacion_actual=data.ubicacion_actual)
    db.add(p)
    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, f"La placa {data.placa} ya existe")
    db.commit()
    db.refresh(p)
    return placa_out(p)
