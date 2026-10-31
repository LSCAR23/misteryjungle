import uuid

import jwt

from app.config import get_settings
from app.enums import Rol
from app.security import create_access_token


def _login(client, username, password):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def test_login_ok_y_case_insensitive(client, make_user):
    u = make_user(rol=Rol.ADMIN, username="Ana.Test", password="clave123")
    r = _login(client, "Ana.Test", "clave123")
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["usuario"]["username"] == "Ana.Test"
    assert body["usuario"]["rol"] == "admin"
    assert body["usuario"]["id"] == str(u.id)
    assert "password_hash" not in body["usuario"]
    assert _login(client, "ANA.test", "clave123").status_code == 200


def test_login_password_incorrecta(client, make_user):
    make_user(username="bob_test", password="clave123")
    r = _login(client, "bob_test", "otra")
    assert r.status_code == 401
    assert r.json()["detail"] == "Usuario o contraseña incorrectos"


def test_login_usuario_desconocido(client):
    r = _login(client, "no_existe_" + uuid.uuid4().hex[:6], "x")
    assert r.status_code == 401
    assert r.json()["detail"] == "Usuario o contraseña incorrectos"


def test_login_usuario_inactivo(client, make_user):
    make_user(username="inactivo_t", password="clave123", activo=False)
    r = _login(client, "inactivo_t", "clave123")
    assert r.status_code == 401
    assert r.json()["detail"] == "Usuario o contraseña incorrectos"


def test_me_con_token(client, empleado_headers):
    r = client.get("/api/auth/me", headers=empleado_headers)
    assert r.status_code == 200
    assert r.json()["rol"] == "empleado"


def test_me_sin_token(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401
    assert r.json()["detail"] == "No autenticado"


def test_me_token_invalido(client):
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer basura"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Sesión inválida o expirada"


def test_me_token_expirado(client, make_user):
    u = make_user()
    token = jwt.encode(
        {"sub": str(u.id), "rol": "empleado", "exp": 1},
        get_settings().jwt_secret,
        algorithm="HS256",
    )
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_me_usuario_inactivo(client, make_user):
    u = make_user(activo=False)
    token = create_access_token(u.id, u.rol)
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_empleado_no_lista_usuarios(client, empleado_headers):
    r = client.get("/api/usuarios", headers=empleado_headers)
    assert r.status_code == 403
    assert r.json()["detail"] == "Solo administradores"


def test_empleado_no_crea_usuarios(client, empleado_headers):
    r = client.post(
        "/api/usuarios",
        headers=empleado_headers,
        json={"username": "nuevo_x", "password": "abcdef", "rol": "empleado"},
    )
    assert r.status_code == 403


def test_usuarios_sin_token(client):
    assert client.get("/api/usuarios").status_code == 401


def test_admin_lista_usuarios(client, admin_headers):
    r = client.get("/api/usuarios", headers=admin_headers)
    assert r.status_code == 200
    nombres = [u["username"].lower() for u in r.json()]
    assert nombres == sorted(nombres)
    assert len(nombres) >= 1


def test_admin_crea_usuario(client, admin_headers):
    nombre = "nuevo_" + uuid.uuid4().hex[:6]
    r = client.post(
        "/api/usuarios",
        headers=admin_headers,
        json={"username": f"  {nombre}  ", "password": "abcdef", "rol": "empleado"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == nombre
    assert body["rol"] == "empleado"
    assert body["activo"] is True
    assert _login(client, nombre, "abcdef").status_code == 200


def test_crear_duplicado_409(client, admin_headers):
    nombre = "dup_" + uuid.uuid4().hex[:6]
    payload = {"username": nombre, "password": "abcdef", "rol": "empleado"}
    assert client.post("/api/usuarios", headers=admin_headers, json=payload).status_code == 201
    r = client.post(
        "/api/usuarios", headers=admin_headers, json={**payload, "username": nombre.upper()}
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "El usuario ya existe"


def test_validacion_422(client, admin_headers):
    base = {"username": "valido_x", "password": "abcdef", "rol": "empleado"}
    for cambio in (
        {"password": "12345"},
        {"username": "ab"},
        {"username": "con espacio"},
        {"username": "raro$"},
        {"rol": "root"},
    ):
        r = client.post("/api/usuarios", headers=admin_headers, json={**base, **cambio})
        assert r.status_code == 422, cambio
