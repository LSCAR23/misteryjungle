import uuid
from datetime import timedelta
from decimal import Decimal

from app.enums import Categoria, EstadoPlaca, EstadoRenta, Rol, Ubicacion
from app.models import Placa, Renta, Usuario, Vehiculo
from app.timeutil import now_utc, rango_dia_cr


def _vehiculo(db):
    sfx = uuid.uuid4().hex[:8]
    v = Vehiculo(marca="Honda", modelo=f"Navi{sfx}", slug=f"honda-navi-{sfx}", cilindrada=110,
                 categoria=Categoria.SCOOTER)
    u = Usuario(username=f"u{sfx}", password_hash="x", rol=Rol.EMPLEADO)
    db.add_all([v, u])
    db.flush()
    return v, u


def _placa(db, v, estado=EstadoPlaca.DISPONIBLE, ubic=Ubicacion.PUERTO_VIEJO, fin=None):
    p = Placa(placa="NUEVA", vehiculo_id=v.id, estado=estado, ubicacion_actual=ubic,
              fecha_hora_finalizacion=fin if estado == EstadoPlaca.RENTADA else None)
    db.add(p)
    db.flush()
    return p


def _renta(db, v, u, p, inicio, fin, estado=EstadoRenta.ACTIVA):
    r = Renta(placa_id=p.id, vehiculo_id=v.id, usuario_id=u.id, inicio=inicio, fin_programado=fin,
              monto=Decimal("20"), desglose="5 horas", estado=estado,
              fin_real=fin if estado != EstadoRenta.ACTIVA else None)
    db.add(r)
    db.flush()
    return r


def _hoy_futuro():
    """Instante futuro dentro del día CR de hoy (punto medio entre ahora y medianoche CR)."""
    now = now_utc()
    _, fin = rango_dia_cr(now)
    return now + (fin - now) / 2


def _vencida(db, v, u, ubic=Ubicacion.NO_ACTUALIZADA):
    fin = now_utc() - timedelta(hours=3)
    p = _placa(db, v, ubic=ubic)
    r = _renta(db, v, u, p, fin - timedelta(hours=5), fin, EstadoRenta.VENCIDA_SIN_RECIBIR)
    return p, r


def test_get_agrupa(client, db, empleado_headers):
    v, u = _vehiculo(db)
    _, r_venc = _vencida(db, v, u)
    fin_hoy = _hoy_futuro()
    p_hoy = _placa(db, v, EstadoPlaca.RENTADA, fin=fin_hoy)
    r_hoy = _renta(db, v, u, p_hoy, now_utc() - timedelta(hours=1), fin_hoy)
    _, fin_dia = rango_dia_cr(now_utc())
    fin_man = fin_dia + timedelta(hours=1)
    p_man = _placa(db, v, EstadoPlaca.RENTADA, fin=fin_man)
    r_man = _renta(db, v, u, p_man, now_utc() - timedelta(hours=1), fin_man)
    p_sin = _placa(db, v, ubic=Ubicacion.NO_ACTUALIZADA)

    res = client.get("/api/recibir", headers=empleado_headers)
    assert res.status_code == 200
    body = res.json()
    assert str(r_venc.id) in [x["id"] for x in body["vencidas"]]
    hoy_ids = [x["id"] for x in body["hoy"]]
    assert str(r_hoy.id) in hoy_ids and str(r_man.id) not in hoy_ids
    sin = {x["id"]: x for x in body["sin_ubicacion"]}
    assert str(p_sin.id) in sin
    assert sin[str(p_sin.id)]["vehiculo"].startswith("Honda Navi")
    # la placa de la renta vencida no se repite en sin_ubicacion
    assert str(r_venc.placa_id) not in sin


def test_recibir_vencida(client, db, empleado_headers):
    v, u = _vehiculo(db)
    p, r = _vencida(db, v, u)
    res = client.post("/api/recibir", headers=empleado_headers,
                      json={"renta_ids": [str(r.id)], "ubicacion": "Playa Negra"})
    assert res.status_code == 200
    assert res.json() == {"rentas_finalizadas": 1, "placas_actualizadas": 1}
    db.refresh(r)
    db.refresh(p)
    assert r.estado == EstadoRenta.FINALIZADA
    assert r.ubicacion_recibida == Ubicacion.PLAYA_NEGRA
    assert r.recibida_por is not None and r.recibida_en is not None
    assert p.ubicacion_actual == Ubicacion.PLAYA_NEGRA
    assert p.estado == EstadoPlaca.DISPONIBLE


def test_recibir_anticipada(client, db, empleado_headers):
    v, u = _vehiculo(db)
    fin = _hoy_futuro()
    p = _placa(db, v, EstadoPlaca.RENTADA, fin=fin)
    r = _renta(db, v, u, p, now_utc() - timedelta(hours=1), fin)
    antes = now_utc()
    res = client.post("/api/recibir", headers=empleado_headers,
                      json={"renta_ids": [str(r.id)], "ubicacion": "B.Azul"})
    assert res.status_code == 200
    db.refresh(r)
    db.refresh(p)
    assert r.estado == EstadoRenta.FINALIZADA
    assert antes <= r.fin_real <= now_utc() and r.fin_real < fin
    assert r.monto == Decimal("20")
    assert p.estado == EstadoPlaca.DISPONIBLE
    assert p.fecha_hora_finalizacion is None
    assert p.ubicacion_actual == Ubicacion.B_AZUL


def test_recibir_vencida_con_placa_rerentada(client, db, empleado_headers):
    v, u = _vehiculo(db)
    p, r_vieja = _vencida(db, v, u)
    fin = _hoy_futuro()
    p.estado = EstadoPlaca.RENTADA
    p.fecha_hora_finalizacion = fin
    p.ubicacion_actual = Ubicacion.PUERTO_VIEJO
    r_nueva = _renta(db, v, u, p, now_utc() - timedelta(minutes=30), fin)
    db.flush()
    res = client.post("/api/recibir", headers=empleado_headers,
                      json={"renta_ids": [str(r_vieja.id)], "ubicacion": "Taller Nico"})
    assert res.status_code == 200
    assert res.json() == {"rentas_finalizadas": 1, "placas_actualizadas": 0}
    db.refresh(r_vieja)
    db.refresh(r_nueva)
    db.refresh(p)
    assert r_vieja.estado == EstadoRenta.FINALIZADA
    assert r_nueva.estado == EstadoRenta.ACTIVA
    assert p.estado == EstadoPlaca.RENTADA
    assert p.ubicacion_actual == Ubicacion.PUERTO_VIEJO
    assert p.fecha_hora_finalizacion is not None


def test_solo_placas(client, db, empleado_headers):
    v, _ = _vehiculo(db)
    p = _placa(db, v, ubic=Ubicacion.NO_ACTUALIZADA)
    res = client.post("/api/recibir", headers=empleado_headers,
                      json={"placa_ids": [str(p.id)], "ubicacion": "Playa Chiquita"})
    assert res.status_code == 200
    assert res.json() == {"rentas_finalizadas": 0, "placas_actualizadas": 1}
    db.refresh(p)
    assert p.ubicacion_actual == Ubicacion.PLAYA_CHIQUITA


def test_placa_rentada_409_y_desconocidos_404(client, db, empleado_headers):
    v, u = _vehiculo(db)
    p = _placa(db, v, EstadoPlaca.RENTADA, fin=_hoy_futuro())
    res = client.post("/api/recibir", headers=empleado_headers,
                      json={"placa_ids": [str(p.id)], "ubicacion": "Playa Chiquita"})
    assert res.status_code == 409
    res = client.post("/api/recibir", headers=empleado_headers,
                      json={"renta_ids": [str(uuid.uuid4())], "ubicacion": "Playa Chiquita"})
    assert res.status_code == 404
    res = client.post("/api/recibir", headers=empleado_headers,
                      json={"placa_ids": [str(uuid.uuid4())], "ubicacion": "Playa Chiquita"})
    assert res.status_code == 404


def test_ubicacion_invalida_422(client, db, empleado_headers):
    v, u = _vehiculo(db)
    _, r = _vencida(db, v, u)
    res = client.post("/api/recibir", headers=empleado_headers,
                      json={"renta_ids": [str(r.id)], "ubicacion": "Ubicación no actualizada"})
    assert res.status_code == 422
    assert res.json()["detail"] == "Elige una ubicación válida"
    res = client.post("/api/recibir", headers=empleado_headers,
                      json={"renta_ids": [str(r.id)], "ubicacion": "Marte"})
    assert res.status_code == 422


def test_ya_finalizada_409(client, db, empleado_headers):
    v, u = _vehiculo(db)
    _, r = _vencida(db, v, u)
    body = {"renta_ids": [str(r.id)], "ubicacion": "Puerto Viejo"}
    assert client.post("/api/recibir", headers=empleado_headers, json=body).status_code == 200
    res = client.post("/api/recibir", headers=empleado_headers, json=body)
    assert res.status_code == 409
    assert res.json()["detail"] == "La renta ya fue recibida"


def test_ids_vacios_422(client, empleado_headers):
    res = client.post("/api/recibir", headers=empleado_headers, json={"ubicacion": "Puerto Viejo"})
    assert res.status_code == 422
    res = client.post("/api/recibir", headers=empleado_headers,
                      json={"renta_ids": [], "placa_ids": [], "ubicacion": "Puerto Viejo"})
    assert res.status_code == 422


def test_requiere_auth(client):
    assert client.get("/api/recibir").status_code == 401
