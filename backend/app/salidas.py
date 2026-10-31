"""Esquemas de salida compartidos entre routers (espejo de los tipos de PLAN §3).

Los montos salen como float (number en JSON), nunca como string.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.enums import Categoria, EstadoPlaca, EstadoRenta, Tarifa, Ubicacion
from app.models import Placa, Renta, Vehiculo

# Orden de tarifas para mostrar (PLAN §2)
ORDEN_TARIFAS = [t.value for t in Tarifa]


class PrecioOut(BaseModel):
    tarifa: Tarifa
    monto: float


class PlacaOut(BaseModel):
    id: UUID
    placa: str
    vehiculo_id: UUID
    estado: EstadoPlaca
    ubicacion_actual: Ubicacion
    fecha_hora_finalizacion: datetime | None


class VehiculoOut(BaseModel):
    id: UUID
    marca: str
    modelo: str
    slug: str
    imagen: str | None
    cilindrada: int
    categoria: Categoria
    cantidad: int
    precios: list[PrecioOut]


class VehiculoDetalleOut(VehiculoOut):
    placas: list[PlacaOut]


class RentaOut(BaseModel):
    id: UUID
    placa_id: UUID
    placa: str
    vehiculo_id: UUID
    vehiculo: str
    categoria: Categoria
    usuario: str
    inicio: datetime
    fin_programado: datetime
    fin_real: datetime | None
    monto: float
    desglose: str
    estado: EstadoRenta
    ubicacion_placa: Ubicacion


class CotizacionItem(BaseModel):
    placa_id: UUID
    vehiculo: str
    placa: str
    monto: float
    desglose: str


class CotizacionOut(BaseModel):
    inicio: datetime
    fin: datetime
    items: list[CotizacionItem]
    total: float


def nombre_vehiculo(v: Vehiculo) -> str:
    return f"{v.marca} {v.modelo}"


def precios_dict(v: Vehiculo) -> dict[str, float]:
    """{codigo_tarifa: monto} listo para services.pricing.cotizar."""
    return {p.tarifa.value: p.monto for p in v.precios}


def placa_out(p: Placa) -> PlacaOut:
    return PlacaOut(
        id=p.id,
        placa=p.placa,
        vehiculo_id=p.vehiculo_id,
        estado=p.estado,
        ubicacion_actual=p.ubicacion_actual,
        fecha_hora_finalizacion=p.fecha_hora_finalizacion,
    )


def _precios_out(v: Vehiculo) -> list[PrecioOut]:
    precios = sorted(v.precios, key=lambda p: ORDEN_TARIFAS.index(p.tarifa.value))
    return [PrecioOut(tarifa=p.tarifa, monto=float(p.monto)) for p in precios]


def vehiculo_out(v: Vehiculo) -> VehiculoOut:
    return VehiculoOut(
        id=v.id,
        marca=v.marca,
        modelo=v.modelo,
        slug=v.slug,
        imagen=v.imagen,
        cilindrada=v.cilindrada,
        categoria=v.categoria,
        cantidad=len(v.placas),
        precios=_precios_out(v),
    )


_ORDEN_ESTADO = {EstadoPlaca.DISPONIBLE: 0, EstadoPlaca.RENTADA: 1, EstadoPlaca.FUERA_DE_SERVICIO: 2}


def vehiculo_detalle_out(v: Vehiculo) -> VehiculoDetalleOut:
    placas = sorted(v.placas, key=lambda p: (_ORDEN_ESTADO.get(p.estado, 9), p.placa.upper(), str(p.id)))
    return VehiculoDetalleOut(**vehiculo_out(v).model_dump(), placas=[placa_out(p) for p in placas])


def renta_out(r: Renta) -> RentaOut:
    return RentaOut(
        id=r.id,
        placa_id=r.placa_id,
        placa=r.placa.placa,
        vehiculo_id=r.vehiculo_id,
        vehiculo=nombre_vehiculo(r.vehiculo),
        categoria=r.vehiculo.categoria,
        usuario=r.usuario.username,
        inicio=r.inicio,
        fin_programado=r.fin_programado,
        fin_real=r.fin_real,
        monto=float(r.monto),
        desglose=r.desglose,
        estado=r.estado,
        ubicacion_placa=r.placa.ubicacion_actual,
    )
