from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.deps import CurrentUser, DbSession
from app.models import Usuario
from app.schemas import LoginIn, LoginOut, UsuarioOut
from app.security import create_access_token, verify_password

router = APIRouter(tags=["auth"])

_MSG = "Usuario o contraseña incorrectos"


@router.post("/auth/login", response_model=LoginOut)
def login(data: LoginIn, db: DbSession):
    usuario = db.scalar(
        select(Usuario).where(func.lower(Usuario.username) == data.username.strip().lower())
    )
    if (
        usuario is None
        or not usuario.activo
        or not verify_password(data.password, usuario.password_hash)
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, _MSG)
    return LoginOut(
        access_token=create_access_token(usuario.id, usuario.rol),
        usuario=UsuarioOut.model_validate(usuario),
    )


@router.get("/auth/me", response_model=UsuarioOut)
def me(usuario: CurrentUser):
    return usuario
