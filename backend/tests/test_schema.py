import pytest
from sqlalchemy.exc import IntegrityError

from app.enums import Categoria, EstadoPlaca, Rol, Ubicacion
from app.models import Placa, Usuario, Vehiculo


def _vehiculo(db, slug="honda-test"):
    v = Vehiculo(
        marca="Honda", modelo="Test", slug=slug, cilindrada=125, categoria=Categoria.SCOOTER
    )
    db.add(v)
    db.flush()
    return v


def test_defaults_placa(db):
    v = _vehiculo(db)
    p = Placa(vehiculo_id=v.id)
    db.add(p)
    db.flush()
    db.refresh(p)
    assert p.placa == "NUEVA"
    assert p.estado == EstadoPlaca.DISPONIBLE
    assert p.ubicacion_actual == Ubicacion.TALLER_NICO
    assert p.fecha_hora_finalizacion is None
    assert p.id is not None and p.created_at is not None
    db.refresh(v)
    assert v.cantidad == 1


def test_check_rentada_requiere_fecha(db):
    v = _vehiculo(db)
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(Placa(vehiculo_id=v.id, estado=EstadoPlaca.RENTADA))
            db.flush()


def test_placas_nueva_duplicadas_ok_y_reales_unicas(db):
    v = _vehiculo(db)
    db.add_all([Placa(vehiculo_id=v.id), Placa(vehiculo_id=v.id)])
    db.add(Placa(vehiculo_id=v.id, placa="MOT 123456"))
    db.flush()
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(Placa(vehiculo_id=v.id, placa="mot 123456"))
            db.flush()


def test_username_unico_case_insensitive(db):
    db.add(Usuario(username="Oscar", password_hash="x", rol=Rol.EMPLEADO))
    db.flush()
    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.add(Usuario(username="oSCAR", password_hash="x", rol=Rol.ADMIN))
            db.flush()
