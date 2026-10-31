"""Verifica el catálogo seed de la migración 0003 (PLAN §5).

La BD de pruebas se migra a head con mock data desactivada, así que sólo
existen los datos del catálogo.
"""
import pytest
from sqlalchemy import func, select

from app.enums import EstadoPlaca
from app.models import Placa, Renta, Vehiculo


def _vehiculo(db, slug: str) -> Vehiculo:
    v = db.scalar(select(Vehiculo).where(Vehiculo.slug == slug))
    assert v is not None, f"falta el vehículo {slug}"
    return v


def test_trece_vehiculos(db):
    assert db.scalar(select(func.count()).select_from(Vehiculo)) == 13


def test_cuarenta_y_ocho_placas(db):
    assert db.scalar(select(func.count()).select_from(Placa)) == 48


def test_placas_nuevas_y_disponibles(db):
    if db.scalar(select(func.count()).select_from(Renta)) > 0:
        pytest.skip("hay rentas en la BD; el chequeo aplica sólo al seed limpio")
    total = db.scalar(select(func.count()).select_from(Placa))
    nuevas = db.scalar(
        select(func.count()).select_from(Placa).where(
            Placa.placa == "NUEVA", Placa.estado == EstadoPlaca.DISPONIBLE
        )
    )
    assert nuevas == total == 48


def test_talon_4x4_sin_dia_ni_5h(db):
    tarifas = {p.tarifa.value for p in _vehiculo(db, "honda-talon-4x4").precios}
    assert "DIA" not in tarifas
    assert "5H" not in tarifas


def test_serie_q_sin_mes_y_marca_isuzu(db):
    v = _vehiculo(db, "isuzu-serie-q")
    assert v.marca == "Isuzu"
    assert "MES" not in {p.tarifa.value for p in v.precios}


def test_navi_ocho_precios_y_seis_placas(db):
    v = _vehiculo(db, "honda-navi")
    assert len(v.precios) == 8
    assert len(v.placas) == 6


def test_pioneer_4x4_cinco_placas(db):
    assert len(_vehiculo(db, "honda-pioneer-4x4").placas) == 5
