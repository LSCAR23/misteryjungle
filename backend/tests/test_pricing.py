"""Tests del cálculo de tarifa (PLAN §4). No requieren base de datos."""
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from app.services.pricing import cotizar

CR = ZoneInfo("America/Costa_Rica")


def cr(y, m, d, h=0, mi=0):
    return datetime(y, m, d, h, mi, tzinfo=CR)


# Precios del catálogo seed (PLAN §5).
NAVI = {"DIA": 30, "5H": 20, "24H": 35, "2D": 60, "3D": 80, "1S": 175, "10D": 200, "MES": 500}
TALON_4X4 = {"24H": 250, "2D": 400, "3D": 500, "1S": 900, "10D": 1100, "MES": 2700}
CAMION = {"DIA": 150, "5H": 100, "24H": 200, "2D": 300, "3D": 450, "1S": 850, "10D": 1000}
CRF300 = {"DIA": 50, "24H": 80, "2D": 140, "3D": 200, "1S": 360, "10D": 460, "MES": 1100}
TRX = {"DIA": 60, "5H": 50, "24H": 80, "2D": 155, "3D": 225, "1S": 490, "10D": 600, "MES": 1300}

INI = cr(2026, 11, 2, 10, 0)

CASOS = [
    ("navi 5H", NAVI, INI, cr(2026, 11, 2, 14, 0), 20, "5 horas"),
    ("navi DIA", NAVI, cr(2026, 11, 2, 8, 30), cr(2026, 11, 2, 17, 0), 30, "Día (8am–5:30pm)"),
    ("navi tarde 5H", NAVI, cr(2026, 11, 2, 18, 0), cr(2026, 11, 2, 22, 0), 20, "5 horas"),
    ("navi 29h", NAVI, INI, INI + timedelta(hours=29), 55, "24 horas + 5 horas"),
    ("navi 30h", NAVI, INI, INI + timedelta(hours=30), 60, "2 días"),
    ("navi 7d", NAVI, INI, INI + timedelta(days=7), 175, "1 semana"),
    ("navi tolerancia", NAVI, INI, INI + timedelta(hours=5, minutes=10), 20, "5 horas"),
    ("talon 3h", TALON_4X4, INI, cr(2026, 11, 2, 13, 0), 250, "24 horas"),
    ("camion 30d", CAMION, INI, INI + timedelta(days=30), 3000, "3 × 10 días"),
    ("crf300 DIA", CRF300, cr(2026, 11, 2, 9, 0), cr(2026, 11, 2, 12, 0), 50, "Día (8am–5:30pm)"),
    ("trx 12d", TRX, INI, INI + timedelta(days=12), 755, "10 días + 2 días"),
]


@pytest.mark.parametrize(
    "precios,inicio,fin,monto,desglose",
    [c[1:] for c in CASOS],
    ids=[c[0] for c in CASOS],
)
def test_tabla_plan(precios, inicio, fin, monto, desglose):
    total, texto = cotizar(precios, inicio, fin)
    assert total == Decimal(monto)
    assert texto == desglose


def test_monto_es_decimal_con_dos_decimales():
    total, _ = cotizar({"5H": 19.995, "24H": 40}, INI, INI + timedelta(hours=2))
    assert isinstance(total, Decimal)
    assert total == Decimal("20.00")
    assert total.as_tuple().exponent == -2


def test_acepta_decimal_y_otras_zonas():
    precios = {k: Decimal(v) for k, v in NAVI.items()}
    utc = ZoneInfo("UTC")
    total, _ = cotizar(precios, INI.astimezone(utc), (INI + timedelta(hours=4)).astimezone(utc))
    assert total == Decimal(20)


def test_dia_no_aplica_si_cruza_medianoche():
    # 16:00 -> 02:00 del día siguiente: DIA no aplica; 24H=35 < 2×5H=40
    total, texto = cotizar(NAVI, cr(2026, 11, 2, 16, 0), cr(2026, 11, 3, 2, 0))
    assert (total, texto) == (Decimal(35), "24 horas")


def test_dia_hasta_1730_inclusive_y_no_despues():
    _, texto = cotizar(CRF300, cr(2026, 11, 2, 9, 0), cr(2026, 11, 2, 17, 30))
    assert texto == "Día (8am–5:30pm)"
    total, texto = cotizar(CRF300, cr(2026, 11, 2, 9, 0), cr(2026, 11, 2, 17, 31))
    assert (total, texto) == (Decimal(80), "24 horas")


def test_empate_prefiere_dia():
    _, texto = cotizar({"DIA": 35, "24H": 35}, cr(2026, 11, 2, 9, 0), cr(2026, 11, 2, 12, 0))
    assert texto == "Día (8am–5:30pm)"


def test_duracion_minima_una_hora():
    total, texto = cotizar(NAVI, INI, INI + timedelta(minutes=1))
    assert (total, texto) == (Decimal(20), "5 horas")


def test_dos_veces_24h_desglose():
    total, texto = cotizar({"24H": 10}, INI, INI + timedelta(hours=48))
    assert (total, texto) == (Decimal(20), "2 × 24 horas")


def test_fin_menor_o_igual_a_inicio():
    with pytest.raises(ValueError):
        cotizar(NAVI, INI, INI)
    with pytest.raises(ValueError):
        cotizar(NAVI, INI, INI - timedelta(hours=1))


def test_requiere_datetimes_con_zona():
    ingenuo = datetime(2026, 11, 2, 10, 0)
    with pytest.raises(ValueError):
        cotizar(NAVI, ingenuo, ingenuo + timedelta(hours=3))
    with pytest.raises(ValueError):
        cotizar(NAVI, INI, ingenuo + timedelta(hours=3))


def test_sin_tarifa_aplicable():
    with pytest.raises(ValueError):
        cotizar({}, INI, INI + timedelta(hours=3))
    # Sólo DIA y la renta no es de mismo día
    with pytest.raises(ValueError):
        cotizar({"DIA": 50}, INI, INI + timedelta(days=2))
