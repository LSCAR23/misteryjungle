from datetime import timedelta

import sqlalchemy as sa

from app.enums import EstadoPlaca, EstadoRenta, Ubicacion
from app.models import Placa, Renta, Vehiculo
from app.timeutil import now_utc


def _placas_navi(db, n=2):
    v = db.scalars(sa.select(Vehiculo).where(Vehiculo.slug == "honda-navi")).one()
    return list(
        db.scalars(sa.select(Placa).where(Placa.vehiculo_id == v.id).order_by(Placa.id).limit(n))
    )


def _fin(horas):
    return (now_utc() + timedelta(hours=horas)).isoformat()


def _rentar(client, h, placas, horas=4):
    r = client.post(
        "/api/rentas",
        json={"placa_ids": [str(p.id) for p in placas], "fin": _fin(horas)},
        headers=h,
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_cotizar(client, empleado_headers, db):
    ps = _placas_navi(db)
    r = client.post(
        "/api/rentas/cotizar",
        json={"placa_ids": [str(p.id) for p in ps], "fin": _fin(4)},
        headers=empleado_headers,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert [i["monto"] for i in d["items"]] == [20, 20]
    assert d["total"] == 40


def test_fin_invalido(client, empleado_headers, db):
    p = _placas_navi(db, 1)[0]
    for fin in (_fin(-1), _fin(0.1), _fin(24 * 91)):
        r = client.post(
            "/api/rentas/cotizar", json={"placa_ids": [str(p.id)], "fin": fin}, headers=empleado_headers
        )
        assert r.status_code == 422
    r = client.post(
        "/api/rentas", json={"placa_ids": [str(p.id)], "fin": _fin(-1)}, headers=empleado_headers
    )
    assert r.status_code == 422


def test_fin_naive(client, empleado_headers, db):
    p = _placas_navi(db, 1)[0]
    naive = (now_utc() + timedelta(hours=4)).replace(tzinfo=None).isoformat()
    r = client.post(
        "/api/rentas/cotizar", json={"placa_ids": [str(p.id)], "fin": naive}, headers=empleado_headers
    )
    assert r.status_code == 422


def test_crear_y_doble_renta(client, empleado_headers, db):
    ps = _placas_navi(db, 3)
    out = _rentar(client, empleado_headers, ps[:2])
    assert len(out) == 2 and all(o["estado"] == "activa" and o["monto"] == 20 for o in out)
    db.expire_all()
    for p in ps[:2]:
        assert p.estado == EstadoPlaca.RENTADA and p.fecha_hora_finalizacion is not None
    assert db.scalar(sa.select(sa.func.count()).select_from(Renta)) == 2

    r = client.post(
        "/api/rentas",
        json={"placa_ids": [str(ps[0].id), str(ps[2].id)], "fin": _fin(4)},
        headers=empleado_headers,
    )
    assert r.status_code == 409
    db.expire_all()
    assert ps[2].estado == EstadoPlaca.DISPONIBLE
    assert db.scalar(sa.select(sa.func.count()).select_from(Renta)) == 2


def test_activas(client, empleado_headers, db):
    ps = _placas_navi(db)
    _rentar(client, empleado_headers, ps[:1], 8)
    _rentar(client, empleado_headers, ps[1:], 4)
    r = client.get("/api/rentas/activas", headers=empleado_headers)
    assert r.status_code == 200
    assert [x["placa_id"] for x in r.json()] == [str(ps[1].id), str(ps[0].id)]


def test_extender_activa(client, empleado_headers, db):
    p = _placas_navi(db, 1)[0]
    vieja = _rentar(client, empleado_headers, [p], 4)[0]
    nuevo_fin = now_utc() + timedelta(hours=10)
    r = client.post(
        f"/api/rentas/{vieja['id']}/extender",
        json={"fin": nuevo_fin.isoformat()},
        headers=empleado_headers,
    )
    assert r.status_code == 201, r.text
    nueva = r.json()
    assert nueva["estado"] == "activa" and nueva["inicio"] == vieja["fin_programado"]
    db.expire_all()
    v = db.get(Renta, vieja["id"])
    assert v.estado == EstadoRenta.FINALIZADA and v.fin_real == v.fin_programado
    assert v.ubicacion_recibida is None and v.recibida_por is not None
    assert p.estado == EstadoPlaca.RENTADA
    assert p.fecha_hora_finalizacion == nuevo_fin
    # ya finalizada
    for suf in ("extender", "extender/cotizar"):
        r = client.post(
            f"/api/rentas/{vieja['id']}/{suf}",
            json={"fin": nuevo_fin.isoformat()},
            headers=empleado_headers,
        )
        assert r.status_code == 409


def _vencer(db, renta_id, placa):
    renta = db.get(Renta, renta_id)
    renta.estado = EstadoRenta.VENCIDA_SIN_RECIBIR
    renta.inicio = now_utc() - timedelta(hours=6)
    renta.fin_programado = now_utc() - timedelta(hours=1)
    renta.fin_real = renta.fin_programado
    placa.estado = EstadoPlaca.DISPONIBLE
    placa.fecha_hora_finalizacion = None
    placa.ubicacion_actual = Ubicacion.NO_ACTUALIZADA
    db.flush()
    return renta


def test_extender_vencida(client, empleado_headers, db):
    p = _placas_navi(db, 1)[0]
    rid = _rentar(client, empleado_headers, [p])[0]["id"]
    _vencer(db, rid, p)
    fin = now_utc() + timedelta(hours=5)
    r = client.post(
        f"/api/rentas/{rid}/extender", json={"fin": fin.isoformat()}, headers=empleado_headers
    )
    assert r.status_code == 201, r.text
    db.expire_all()
    assert p.estado == EstadoPlaca.RENTADA and p.fecha_hora_finalizacion == fin
    assert db.get(Renta, rid).estado == EstadoRenta.FINALIZADA


def test_extender_vencida_placa_rerentada(client, empleado_headers, db):
    p = _placas_navi(db, 1)[0]
    rid = _rentar(client, empleado_headers, [p])[0]["id"]
    _vencer(db, rid, p)
    _rentar(client, empleado_headers, [p], 3)
    r = client.post(f"/api/rentas/{rid}/extender", json={"fin": _fin(8)}, headers=empleado_headers)
    assert r.status_code == 409
    assert r.json()["detail"] == "La placa ya no está disponible para extender"
    db.expire_all()
    assert db.get(Renta, rid).estado == EstadoRenta.VENCIDA_SIN_RECIBIR


def test_extender_cotizar(client, empleado_headers, db):
    p = _placas_navi(db, 1)[0]
    vieja = _rentar(client, empleado_headers, [p], 4)[0]
    url = f"/api/rentas/{vieja['id']}/extender/cotizar"
    r = client.post(url, json={"fin": _fin(9)}, headers=empleado_headers)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["inicio"] == vieja["fin_programado"] and len(d["items"]) == 1
    assert d["total"] == d["items"][0]["monto"] > 0
    r = client.post(url, json={"fin": _fin(4)}, headers=empleado_headers)
    assert r.status_code == 422
    r = client.post(
        "/api/rentas/00000000-0000-0000-0000-000000000000/extender/cotizar",
        json={"fin": _fin(9)},
        headers=empleado_headers,
    )
    assert r.status_code == 404
