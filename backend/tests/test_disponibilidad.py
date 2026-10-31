from datetime import timedelta

from sqlalchemy import select

from app.enums import EstadoPlaca, EstadoRenta, Ubicacion
from app.models import Placa, Renta, Usuario, Vehiculo
from app.timeutil import now_utc


def _placas_de(db, categoria):
    return db.scalars(
        select(Placa).join(Vehiculo).where(Vehiculo.categoria == categoria).order_by(Placa.id)
    ).all()


def test_categorias(client, db, empleado_headers):
    r = client.get("/api/disponibilidad/categorias", headers=empleado_headers)
    assert r.status_code == 200
    data = r.json()
    assert [c["categoria"] for c in data] == ["Scooter", "Moto", "ATV", "UTV", "Camion"]
    assert sum(c["total"] for c in data) == 48
    assert all(c["disponibles"] == c["total"] for c in data)


def test_categorias_cambian_con_estados(client, db, empleado_headers):
    ps = _placas_de(db, "UTV")
    ps[0].estado = EstadoPlaca.RENTADA
    ps[0].fecha_hora_finalizacion = now_utc() + timedelta(hours=5)
    ps[1].estado = EstadoPlaca.FUERA_DE_SERVICIO
    db.flush()
    data = {c["categoria"]: c for c in client.get("/api/disponibilidad/categorias", headers=empleado_headers).json()}
    assert data["UTV"]["disponibles"] == data["UTV"]["total"] - 2
    assert sum(c["total"] for c in data.values()) == 48


def test_vehiculos_utv(client, db, admin_headers):
    r = client.get("/api/disponibilidad", params={"categoria": "UTV"}, headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 4
    assert all(v["categoria"] == "UTV" for v in data)
    for v in data:
        assert v["disponibles"] == v["cantidad"]
        assert sum(u["disponibles"] for u in v["por_ubicacion"]) == v["disponibles"]
    assert [v["disponibles"] for v in data] == sorted((v["disponibles"] for v in data), reverse=True)


def test_por_ubicacion_y_cero_disponibles(client, db, empleado_headers):
    vs = db.scalars(select(Vehiculo).where(Vehiculo.categoria == "UTV")).all()
    objetivo = vs[0]
    for i, p in enumerate(objetivo.placas):
        p.ubicacion_actual = Ubicacion.PUERTO_VIEJO if i < 2 else Ubicacion.PLAYA_NEGRA
    otro = vs[1]
    for p in otro.placas:
        p.estado = EstadoPlaca.FUERA_DE_SERVICIO
    db.flush()
    data = client.get("/api/disponibilidad", params={"categoria": "UTV"}, headers=empleado_headers).json()
    assert len(data) == 4
    d = {v["id"]: v for v in data}
    pu = d[str(objetivo.id)]["por_ubicacion"]
    n = len(objetivo.placas)
    esperado = [("Puerto Viejo", 2)] + ([("Playa Negra", n - 2)] if n > 2 else [])
    esperado.sort(key=lambda x: (-x[1], x[0]))
    assert [(u["ubicacion"], u["disponibles"]) for u in pu] == esperado
    cero = d[str(otro.id)]
    assert cero["disponibles"] == 0 and cero["por_ubicacion"] == []
    assert [v["disponibles"] for v in data] == sorted((v["disponibles"] for v in data), reverse=True)


def test_categoria_invalida_o_faltante(client, empleado_headers):
    assert client.get("/api/disponibilidad", headers=empleado_headers).status_code == 422
    r = client.get("/api/disponibilidad", params={"categoria": "Bici"}, headers=empleado_headers)
    assert r.status_code == 422


def test_sin_autenticar(client):
    assert client.get("/api/disponibilidad/categorias").status_code == 401
    assert client.get("/api/disponibilidad", params={"categoria": "UTV"}).status_code == 401


def test_renta_vencida_se_sincroniza(client, db, empleado_headers):
    veh = db.scalars(select(Vehiculo).where(Vehiculo.categoria == "UTV")).first()
    placa = veh.placas[0]
    ahora = now_utc()
    placa.estado = EstadoPlaca.RENTADA
    placa.fecha_hora_finalizacion = ahora - timedelta(hours=1)
    usuario = db.scalars(select(Usuario)).first()
    db.add(
        Renta(
            placa_id=placa.id,
            vehiculo_id=veh.id,
            usuario_id=usuario.id,
            inicio=ahora - timedelta(hours=6),
            fin_programado=ahora - timedelta(hours=1),
            monto=50,
            desglose="5 horas",
            estado=EstadoRenta.ACTIVA,
        )
    )
    db.flush()
    data = client.get("/api/disponibilidad", params={"categoria": "UTV"}, headers=empleado_headers).json()
    v = next(x for x in data if x["id"] == str(veh.id))
    assert v["disponibles"] == v["cantidad"]
    assert {"ubicacion": "Ubicación no actualizada", "disponibles": 1} in v["por_ubicacion"]
    db.refresh(placa)
    assert placa.estado == EstadoPlaca.DISPONIBLE
