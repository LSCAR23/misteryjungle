import uuid
from datetime import timedelta

from app.enums import EstadoPlaca
from app.models import Placa
from app.timeutil import now_utc

PRECIOS = [{"tarifa": "24H", "monto": 30}, {"tarifa": "5H", "monto": 20}]
BAZUL = {"ubicacion_actual": "B.Azul"}


def _payload(**kw):
    base = {
        "marca": "Yamaha",
        "modelo": "Zuma Test",
        "cilindrada": 125,
        "categoria": "Scooter",
        "precios": PRECIOS,
        "placas": [
            {"ubicacion_actual": "Puerto Viejo"},
            {"placa": "  ab 1234 ", "ubicacion_actual": "B.Azul"},
        ],
    }
    base.update(kw)
    return base


def _primero(client, h):
    return client.get("/api/vehiculos", headers=h).json()[0]


def _placas(client, h):
    v = _primero(client, h)
    return client.get(f"/api/vehiculos/{v['id']}", headers=h).json()["placas"]


def test_listar(client, empleado_headers):
    r = client.get("/api/vehiculos", headers=empleado_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 13
    assert sum(v["cantidad"] for v in data) == 48
    assert "placas" not in data[0]


def test_listar_requiere_auth(client):
    assert client.get("/api/vehiculos").status_code == 401


def test_filtro_categoria(client, empleado_headers):
    r = client.get("/api/vehiculos?categoria=Scooter", headers=empleado_headers)
    assert r.status_code == 200
    assert r.json() and all(v["categoria"] == "Scooter" for v in r.json())
    assert client.get("/api/vehiculos?categoria=Nada", headers=empleado_headers).status_code == 422


def test_detalle(client, empleado_headers):
    v = _primero(client, empleado_headers)
    r = client.get(f"/api/vehiculos/{v['id']}", headers=empleado_headers)
    assert r.status_code == 200
    d = r.json()
    assert d["cantidad"] == len(d["placas"]) > 0
    orden = ["5H", "DIA", "24H", "2D", "3D", "1S", "10D", "MES"]
    tarifas = [p["tarifa"] for p in d["precios"]]
    assert tarifas == sorted(tarifas, key=orden.index)
    assert isinstance(d["precios"][0]["monto"], (int, float))


def test_detalle_404(client, empleado_headers):
    r = client.get(f"/api/vehiculos/{uuid.uuid4()}", headers=empleado_headers)
    assert r.status_code == 404
    assert r.json()["detail"] == "Vehículo no encontrado"


def test_crear_vehiculo(client, admin_headers):
    r = client.post("/api/vehiculos", json=_payload(), headers=admin_headers)
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["slug"] == "yamaha-zuma-test"
    assert d["imagen"] == "/vehiculos/yamaha-zuma-test.png"
    assert d["cantidad"] == 2
    assert [p["tarifa"] for p in d["precios"]] == ["5H", "24H"]
    assert sorted(p["placa"] for p in d["placas"]) == ["AB 1234", "NUEVA"]
    assert all(p["estado"] == "Disponible" for p in d["placas"])
    assert len(client.get("/api/vehiculos", headers=admin_headers).json()) == 14


def test_crear_imagen_personalizada(client, admin_headers):
    r = client.post("/api/vehiculos", json=_payload(imagen="/vehiculos/x.png"), headers=admin_headers)
    assert r.status_code == 201
    assert r.json()["imagen"] == "/vehiculos/x.png"


def test_slug_duplicado(client, admin_headers):
    slugs = [
        client.post("/api/vehiculos", json=_payload(placas=[BAZUL]), headers=admin_headers).json()["slug"]
        for _ in range(3)
    ]
    assert slugs == ["yamaha-zuma-test", "yamaha-zuma-test-2", "yamaha-zuma-test-3"]


def test_crear_empleado_403(client, empleado_headers):
    r = client.post("/api/vehiculos", json=_payload(), headers=empleado_headers)
    assert r.status_code == 403


def test_crear_validaciones(client, admin_headers):
    for body in (
        _payload(precios=[]),
        _payload(placas=[]),
        _payload(precios=[{"tarifa": "5H", "monto": 0}]),
        _payload(precios=[{"tarifa": "5H", "monto": 5}, {"tarifa": "5H", "monto": 6}]),
        _payload(placas=[{"ubicacion_actual": "Ubicación no actualizada"}]),
        _payload(placas=[{"ubicacion_actual": "Marte"}]),
        _payload(cilindrada=0),
        _payload(placas=[BAZUL] * 51),
    ):
        assert client.post("/api/vehiculos", json=body, headers=admin_headers).status_code == 422


def test_crear_placa_real_duplicada(client, admin_headers):
    assert client.post("/api/vehiculos", json=_payload(), headers=admin_headers).status_code == 201
    r = client.post(
        "/api/vehiculos",
        json=_payload(modelo="Otro", placas=[{"placa": "ab 1234", "ubicacion_actual": "B.Azul"}]),
        headers=admin_headers,
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "La placa AB 1234 ya existe"
    r = client.post(
        "/api/vehiculos",
        json=_payload(modelo="Otro2", placas=[{"placa": "zz1", "ubicacion_actual": "B.Azul"}] * 2),
        headers=admin_headers,
    )
    assert r.status_code == 409


def test_agregar_placa(client, admin_headers, empleado_headers):
    v = _primero(client, admin_headers)
    url = f"/api/vehiculos/{v['id']}/placas"
    assert client.post(url, json=BAZUL, headers=empleado_headers).status_code == 403
    r = client.post(url, json={"placa": "mot 99999", **BAZUL}, headers=admin_headers)
    assert r.status_code == 201
    assert r.json()["placa"] == "MOT 99999"
    r = client.post(url, json={"ubicacion_actual": "Taller Nico"}, headers=admin_headers)
    assert r.status_code == 201
    assert r.json()["placa"] == "NUEVA"
    assert client.post(url, json={"placa": "MOT 99999", **BAZUL}, headers=admin_headers).status_code == 409
    d = client.get(f"/api/vehiculos/{v['id']}", headers=admin_headers).json()
    assert d["cantidad"] == v["cantidad"] + 2
    r = client.post(f"/api/vehiculos/{uuid.uuid4()}/placas", json=BAZUL, headers=admin_headers)
    assert r.status_code == 404


def test_patch_placa(client, admin_headers, empleado_headers):
    p = _placas(client, admin_headers)[0]
    url = f"/api/placas/{p['id']}"
    assert client.patch(url, json={"placa": "x"}, headers=empleado_headers).status_code == 403
    r = client.patch(url, json={"placa": " mot 123456 ", "ubicacion_actual": "Playa Negra"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["placa"] == "MOT 123456"
    assert r.json()["ubicacion_actual"] == "Playa Negra"
    assert client.patch(f"/api/placas/{uuid.uuid4()}", json={"placa": "A"}, headers=admin_headers).status_code == 404
    otra = _placas(client, admin_headers)[1]
    r = client.patch(f"/api/placas/{otra['id']}", json={"placa": "MOT 123456"}, headers=admin_headers)
    assert r.status_code == 409


def test_patch_ubicacion_no_actualizada_422(client, admin_headers):
    p = _placas(client, admin_headers)[0]
    r = client.patch(
        f"/api/placas/{p['id']}", json={"ubicacion_actual": "Ubicación no actualizada"}, headers=admin_headers
    )
    assert r.status_code == 422


def test_patch_ubicacion_rentada_409(client, admin_headers, db):
    p = _placas(client, admin_headers)[0]
    obj = db.get(Placa, uuid.UUID(p["id"]))
    obj.estado = EstadoPlaca.RENTADA
    obj.fecha_hora_finalizacion = now_utc() + timedelta(days=1)
    db.flush()
    r = client.patch(f"/api/placas/{p['id']}", json={"ubicacion_actual": "B.Azul"}, headers=admin_headers)
    assert r.status_code == 409


def test_estado_fuera_servicio_y_habilitar(client, admin_headers, empleado_headers):
    ids = [p["id"] for p in _placas(client, admin_headers)[:2]]
    body = {"placa_ids": ids, "accion": "fuera_servicio"}
    assert client.post("/api/placas/estado", json=body, headers=empleado_headers).status_code == 403
    r = client.post("/api/placas/estado", json=body, headers=admin_headers)
    assert r.status_code == 200
    assert [p["estado"] for p in r.json()] == ["Fuera de Servicio"] * 2
    r = client.post("/api/placas/estado", json={"placa_ids": ids, "accion": "habilitar"}, headers=admin_headers)
    assert r.status_code == 200
    assert [p["estado"] for p in r.json()] == ["Disponible"] * 2


def test_estado_mixto_409_sin_cambios(client, admin_headers, db):
    ps = _placas(client, admin_headers)
    a, b = ps[0]["id"], ps[1]["id"]
    r = client.post("/api/placas/estado", json={"placa_ids": [a], "accion": "fuera_servicio"}, headers=admin_headers)
    assert r.status_code == 200
    for accion in ("fuera_servicio", "habilitar"):
        r = client.post("/api/placas/estado", json={"placa_ids": [a, b], "accion": accion}, headers=admin_headers)
        assert r.status_code == 409
    db.expire_all()
    assert db.get(Placa, uuid.UUID(a)).estado == EstadoPlaca.FUERA_DE_SERVICIO
    assert db.get(Placa, uuid.UUID(b)).estado == EstadoPlaca.DISPONIBLE
    r = client.post("/api/placas/estado", json={"placa_ids": [str(uuid.uuid4())], "accion": "habilitar"}, headers=admin_headers)
    assert r.status_code == 404
    r = client.post("/api/placas/estado", json={"placa_ids": [], "accion": "habilitar"}, headers=admin_headers)
    assert r.status_code == 422
