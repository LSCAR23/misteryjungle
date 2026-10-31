from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
import sqlalchemy as sa

from app.seed.mock_data import generar

CR = ZoneInfo("America/Costa_Rica")
FIXED = datetime(2026, 10, 31, 10, 0, tzinfo=CR)


def _reset(conn):
    conn.execute(sa.text("DELETE FROM rentas"))
    conn.execute(
        sa.text(
            "UPDATE placas SET placa='NUEVA', estado='Disponible', "
            "ubicacion_actual='Puerto Viejo', fecha_hora_finalizacion=NULL"
        )
    )


def _q(conn, sql, **kw):
    return conn.execute(sa.text(sql), kw).all()


def test_estado_generado(db):
    conn = db.connection()
    generar(conn, FIXED)

    rentadas = _q(conn, "SELECT id, fecha_hora_finalizacion FROM placas WHERE estado='Rentada'")
    assert len(rentadas) == 12
    hoy = 0
    for pid, fecha in rentadas:
        activas = _q(
            conn, "SELECT fin_programado FROM rentas WHERE placa_id=:p AND estado='activa'", p=pid
        )
        assert len(activas) == 1
        assert activas[0][0] == fecha
        assert fecha > FIXED
        if fecha.astimezone(CR).date() == FIXED.date():
            hoy += 1
    assert hoy == 4

    vencidas = _q(
        conn,
        "SELECT p.estado, p.ubicacion_actual, r.fin_real, r.fin_programado FROM rentas r "
        "JOIN placas p ON p.id=r.placa_id WHERE r.estado='vencida_sin_recibir'",
    )
    assert len(vencidas) == 2
    for estado, ub, fin_real, fin in vencidas:
        assert estado == "Disponible" and ub == "Ubicación no actualizada"
        assert fin_real == fin and fin < FIXED

    fuera = _q(conn, "SELECT ubicacion_actual FROM placas WHERE estado='Fuera de Servicio'")
    assert len(fuera) == 3 and all(u[0] == "Taller Nico" for u in fuera)

    assert _q(conn, "SELECT count(*) FROM rentas WHERE estado='finalizada'")[0][0] >= 200
    assert _q(conn, "SELECT count(*) FROM rentas WHERE inicio > :n", n=FIXED)[0][0] == 0
    assert _q(
        conn,
        "SELECT count(*) FROM rentas WHERE estado='finalizada' AND fin_programado > :n",
        n=FIXED - timedelta(days=1),
    )[0][0] == 0
    assert _q(conn, "SELECT count(*) FROM placas WHERE placa <> 'NUEVA'")[0][0] == 20

    slugs = {
        r[0]
        for r in _q(
            conn,
            "SELECT v.slug FROM placas p JOIN vehiculos v ON v.id=p.vehiculo_id "
            "WHERE p.estado='Rentada'",
        )
    }
    assert "honda-navi" in slugs and "isuzu-serie-q" in slugs
    assert slugs & {"honda-talon-4x4", "honda-talon-4wd"}


def test_cuatro_terminan_hoy_por_la_tarde(db):
    conn = db.connection()
    ahora = datetime(2026, 10, 31, 16, 0, tzinfo=CR)
    generar(conn, ahora)
    fines = _q(conn, "SELECT fin_programado FROM rentas WHERE estado='activa'")
    hoy = [f[0] for f in fines if f[0].astimezone(CR).date() == ahora.date()]
    assert len(hoy) == 4
    assert all(f > ahora for f in hoy)


def test_determinista(db):
    conn = db.connection()
    generar(conn, FIXED)
    a = _q(conn, "SELECT sum(monto), count(*) FROM rentas")[0]
    _reset(conn)
    generar(conn, FIXED)
    b = _q(conn, "SELECT sum(monto), count(*) FROM rentas")[0]
    assert a == b


def test_falla_si_hay_rentas(db):
    conn = db.connection()
    generar(conn, FIXED)
    with pytest.raises(RuntimeError):
        generar(conn, FIXED)
