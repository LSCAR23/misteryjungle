import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.enums import Categoria, EstadoPlaca, EstadoRenta, Rol, Ubicacion
from app.models import Placa, Renta, Usuario, Vehiculo
from app.services.vencimientos import sincronizar_vencidas
from app.timeutil import CR, mes_cr, rango_dia_cr

NOW = datetime(2026, 10, 30, 18, 0, tzinfo=timezone.utc)


def _base(db):
    sfx = uuid.uuid4().hex[:8]
    v = Vehiculo(marca="X", modelo="Y", slug=f"x-y-{sfx}", cilindrada=125, categoria=Categoria.MOTO)
    u = Usuario(username=f"u{sfx}", password_hash="x", rol=Rol.EMPLEADO)
    db.add_all([v, u])
    db.flush()
    return v, u


def _rentada(db, v, u, fin, estado_placa=EstadoPlaca.RENTADA):
    p = Placa(
        placa="NUEVA",
        vehiculo_id=v.id,
        estado=estado_placa,
        ubicacion_actual=Ubicacion.PUERTO_VIEJO,
        fecha_hora_finalizacion=fin if estado_placa == EstadoPlaca.RENTADA else None,
    )
    db.add(p)
    db.flush()
    r = Renta(
        placa_id=p.id, vehiculo_id=v.id, usuario_id=u.id,
        inicio=fin - timedelta(hours=5), fin_programado=fin,
        monto=Decimal("20"), desglose="5 horas",
    )
    db.add(r)
    db.flush()
    return p, r


def test_vencida(db):
    v, u = _base(db)
    fin = NOW - timedelta(minutes=1)
    p, r = _rentada(db, v, u, fin)
    assert sincronizar_vencidas(db, NOW) == 1
    db.refresh(p)
    db.refresh(r)
    assert r.estado == EstadoRenta.VENCIDA_SIN_RECIBIR
    assert r.fin_real == fin
    assert p.estado == EstadoPlaca.DISPONIBLE
    assert p.ubicacion_actual == Ubicacion.NO_ACTUALIZADA
    assert p.fecha_hora_finalizacion is None
    assert sincronizar_vencidas(db, NOW) == 0


def test_no_vencida_intacta(db):
    v, u = _base(db)
    fin = NOW + timedelta(hours=1)
    p, r = _rentada(db, v, u, fin)
    assert sincronizar_vencidas(db, NOW) == 0
    db.refresh(p)
    db.refresh(r)
    assert r.estado == EstadoRenta.ACTIVA and r.fin_real is None
    assert p.estado == EstadoPlaca.RENTADA
    assert p.ubicacion_actual == Ubicacion.PUERTO_VIEJO


def test_fuera_de_servicio_intacta(db):
    v, u = _base(db)
    p = Placa(vehiculo_id=v.id, estado=EstadoPlaca.FUERA_DE_SERVICIO, ubicacion_actual=Ubicacion.TALLER_NICO)
    db.add(p)
    db.flush()
    sincronizar_vencidas(db, NOW)
    db.refresh(p)
    assert p.estado == EstadoPlaca.FUERA_DE_SERVICIO
    assert p.ubicacion_actual == Ubicacion.TALLER_NICO


def test_placa_rerentada_no_se_toca(db):
    v, u = _base(db)
    p, vieja = _rentada(db, v, u, NOW - timedelta(hours=1))
    # la placa fue re-rentada con una renta nueva aún vigente
    nuevo_fin = NOW + timedelta(hours=3)
    p.fecha_hora_finalizacion = nuevo_fin
    nueva = Renta(
        placa_id=p.id, vehiculo_id=v.id, usuario_id=u.id,
        inicio=NOW, fin_programado=nuevo_fin, monto=Decimal("20"), desglose="5 horas",
    )
    db.add(nueva)
    db.flush()
    assert sincronizar_vencidas(db, NOW) == 1
    db.refresh(p)
    db.refresh(vieja)
    db.refresh(nueva)
    assert vieja.estado == EstadoRenta.VENCIDA_SIN_RECIBIR
    assert nueva.estado == EstadoRenta.ACTIVA
    assert p.estado == EstadoPlaca.RENTADA
    assert p.fecha_hora_finalizacion == nuevo_fin


def test_rango_dia_cr_medianoche():
    now = datetime(2026, 10, 31, 23, 30, tzinfo=CR)
    ini, fin = rango_dia_cr(now)
    assert ini == datetime(2026, 10, 31, 6, 0, tzinfo=timezone.utc)
    assert fin == datetime(2026, 11, 1, 6, 0, tzinfo=timezone.utc)
    # 05:59 UTC del 1 nov sigue siendo 31 oct en CR
    ini2, _ = rango_dia_cr(datetime(2026, 11, 1, 5, 59, tzinfo=timezone.utc))
    assert ini2 == ini
    ini3, _ = rango_dia_cr(datetime(2026, 11, 1, 6, 0, tzinfo=timezone.utc))
    assert ini3 == fin


def test_mes_cr():
    assert mes_cr(datetime(2026, 11, 1, 5, 0, tzinfo=timezone.utc)) == "2026-10"
    assert mes_cr(datetime(2026, 11, 1, 6, 0, tzinfo=timezone.utc)) == "2026-11"
