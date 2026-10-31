from datetime import datetime  # noqa: F401
from uuid import UUID  # noqa: F401

from pydantic import BaseModel, ConfigDict, Field, field_validator  # noqa: F401

from app.enums import Rol  # noqa: F401

# --- auth ---
class LoginIn(BaseModel):
    username: str
    password: str


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    rol: Rol
    activo: bool
    created_at: datetime


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


# --- usuarios ---
class UsuarioCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9._-]+$")
    password: str = Field(min_length=6, max_length=100)
    rol: Rol

    @field_validator("username", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v


# --- vehiculos/placas ---

# --- disponibilidad ---

# --- rentas ---

# --- recibir ---

# --- metricas ---
