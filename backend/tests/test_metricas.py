import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.enums import Categoria, EstadoPlaca, EstadoRenta, Rol, Ubicacion
from app.models import Placa, Renta, Vehiculo
from app.services.metricas import calcular
from app.timeutil import CR

NOW = datetime(2026, 10, 30, 12, 0, tzinfo=CR)


def _cr(y, m, d, h=10):
    return datetime(y, m, d, h, 0, tzinfo=CR).astimezone(timezone.utc)


def _veh(db, modelo, cat=Categoria.SCOOTER):
    v = Vehiculo(marca="Honda", modelo=modelo, slug=f"t-{modelo.lower()}-{uuid.uuid4().hex[:6]}",
                 cilindrada=100, categoria=cat)
    db.add(v)
    db.flush()
    return v


def _placa(db, v, estado=EstadoPlaca.DISPONIBLE, ubic=Ubicacion.PUERTO_VIEJO):
    p = Placa(
        vehiculo_id=v.id,
        estado=estado,
        ubicacion_actual=ubic,
        fecha_hora_finalizacion=NOW + timedelta(days=1) if estado == EstadoPlaca.RENTADA else None,
    )
    db.add(p)
    db.flush()
    return p


def _renta(db, p, u, inicio, monto, horas=24, estado=EstadoRenta.FINALIZADA):
    r = Renta(placa_id=p.id, vehiculo_id=p.vehiculo_id, usuario_id=u.id, inicio=inicio,
              fin_programado=inicio + timedelta(hours=horas), monto=Decimal(monto),
              desglose="x", estado=estado)
    db.add(r)
    db.flush()
    return r


def _escenario(db, make_user):
    oscar = make_user(rol=Rol.EMPLEADO, username="zz_oscar")
    ivan = make_user(rol=Rol.ADMIN, username="zz_ivan")
    navi, atv = _veh(db, "Navi"), _veh(db, "Rincon", Categoria.ATV)
    p1 = _placa(db, navi)
    _placa(db, navi, EstadoPlaca.RENTADA)
    p3 = _placa(db, atv, EstadoPlaca.FUERA_DE_SERVICIO)
    # octubre 2026 (mes actual): 2 navi (35+35) oscar, 1 atv (100) ivan
    _renta(db, p1, oscar, _cr(2026, 10, 5), "35", 24)
    _renta(db, p1, oscar, _cr(2026, 10, 7), "35", 24)
    _renta(db, p3, ivan, _cr(2026, 10, 9), "100", 24)
    # septiembre 2026: 1 navi 60 (48 h)
    _renta(db, p1, ivan, _cr(2026, 9, 15), "60", 48)
    # fuera de rango
    _renta(db, p1, ivan, _cr(2024, 1, 1), "999")


def test_calcular(db, make_user):
    _escenario(db, make_user)
    m = calcular(db, NOW, 3)
    assert [x["mes"] for x in m["por_mes"]] == ["2026-08", "2026-09", "2026-10"]
    assert m["por_mes"][0] == {"mes": "2026-08", "rentas": 0, "ingresos": 0.0}
    assert m["por_mes"][2] == {"mes": "2026-10", "rentas": 3, "ingresos": 170.0}
    assert m["mes_top"] == {"mes": "2026-10", "rentas": 3, "ingresos": 170.0}
    k = m["kpis"]
    assert k["ingresos_mes_actual"] == 170.0 and k["ingresos_mes_anterior"] == 60.0
    assert k["rentas_mes_actual"] == 3
    assert m["vehiculo_mas_popular"] == {"vehiculo": "Honda Navi", "rentas": 3}
    assert m["vehiculo_mas_ingresos"] == {"vehiculo": "Honda Navi", "ingresos": 130.0}
    assert [v["vehiculo"] for v in m["por_vehiculo"]] == ["Honda Navi", "Honda Rincon"]
    assert m["por_vehiculo"][0]["ingresos"] == 130.0 and m["por_vehiculo"][0]["categoria"] == "Scooter"
    assert m["usuario_top"] == {"usuario": "zz_ivan", "rentas": 2, "ingresos": 160.0}  # empate en rentas, gana por ingresos
    assert sum(d["rentas"] for d in m["por_dia_semana"]) == 4
    assert [d["dia"] for d in m["por_dia_semana"]] == ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    assert k["ticket_promedio"] == 57.5  # (35+35+100+60)/4
    assert k["duracion_promedio_horas"] == 30.0  # (24*3+48)/4
    assert {c["categoria"] for c in m["por_categoria"]} == {"Scooter", "ATV"}


def test_ocupacion_y_ubicaciones(db, make_user):
    _escenario(db, make_user)
    m = calcular(db, NOW, 12)
    k = m["kpis"]
    total, rent, fuera = k["unidades_total"], k["unidades_rentadas"], k["unidades_fuera_servicio"]
    assert rent >= 1 and fuera >= 1
    assert k["ocupacion_actual"] == round(rent / (total - fuera), 4)
    assert len(m["por_mes"]) == 12
    ub = {x["ubicacion"]: x["disponibles"] for x in m["disponibles_por_ubicacion"]}
    assert ub["Puerto Viejo"] >= 1


def test_vacio_y_pendientes(db, make_user):
    m = calcular(db, NOW, 2)
    assert m["vehiculo_mas_popular"] is None and m["usuario_top"] is None
    assert m["mes_top"] is None and m["vehiculo_mas_ingresos"] is None
    assert m["kpis"]["ticket_promedio"] == 0.0
    base = m["kpis"]["pendientes_recibir"]
    u = make_user()
    v = _veh(db, "Pend")
    _placa(db, v, ubic=Ubicacion.NO_ACTUALIZADA)
    q = _placa(db, v, ubic=Ubicacion.NO_ACTUALIZADA)
    _renta(db, q, u, _cr(2026, 10, 1), "20", 5, EstadoRenta.VENCIDA_SIN_RECIBIR)
    # p cuenta por su ubicación; q una sola vez (por su renta vencida)
    assert calcular(db, NOW, 2)["kpis"]["pendientes_recibir"] == base + 2


def test_limite_de_mes_en_cr(db, make_user):
    u = make_user()
    p = _placa(db, _veh(db, "Lim"))
    # 31 oct 20:00 CR = 1 nov 02:00 UTC -> sigue siendo octubre en CR
    _renta(db, p, u, _cr(2026, 10, 31, 20), "10")
    m = calcular(db, NOW, 1)
    assert m["por_mes"] == [{"mes": "2026-10", "rentas": 1, "ingresos": 10.0}]
    assert m["kpis"]["ingresos_mes_anterior"] == 0.0


def test_endpoint(client, db, make_user, admin_headers, empleado_headers):
    _escenario(db, make_user)
    assert client.get("/api/metricas", headers=empleado_headers).status_code == 403
    assert client.get("/api/metricas").status_code == 401
    assert client.get("/api/metricas?meses=0", headers=admin_headers).status_code == 422
    assert client.get("/api/metricas?meses=25", headers=admin_headers).status_code == 422
    r = client.get("/api/metricas?meses=6", headers=admin_headers)
    assert r.status_code == 200
    j = r.json()
    assert len(j["por_mes"]) == 6
    assert isinstance(j["kpis"]["ingresos_mes_actual"], (int, float))
    assert isinstance(j["kpis"]["ocupacion_actual"], float)
    assert all(isinstance(x["ingresos"], (int, float)) for x in j["por_vehiculo"])
