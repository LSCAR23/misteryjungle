from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.deps import AdminUser, DbSession
from app.models import Usuario
from app.schemas import UsuarioCreate, UsuarioOut
from app.security import hash_password

router = APIRouter(tags=["usuarios"])

_DUP = "El usuario ya existe"


@router.get("/usuarios", response_model=list[UsuarioOut])
def listar(_: AdminUser, db: DbSession):
    return db.scalars(select(Usuario).order_by(func.lower(Usuario.username))).all()


@router.post("/usuarios", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def crear(data: UsuarioCreate, _: AdminUser, db: DbSession):
    if db.scalar(select(Usuario.id).where(func.lower(Usuario.username) == data.username.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, _DUP)
    usuario = Usuario(
        username=data.username,
        password_hash=hash_password(data.password),
        rol=data.rol,
    )
    db.add(usuario)
    try:
        with db.begin_nested():
            db.flush()
    except IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, _DUP)
    db.commit()
    db.refresh(usuario)
    return usuario
