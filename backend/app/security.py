from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import get_settings

ALGORITMO = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id, rol) -> str:
    settings = get_settings()
    rol_valor = getattr(rol, "value", rol)
    payload = {
        "sub": str(user_id),
        "rol": rol_valor,
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITMO)


def decode_token(token: str) -> dict:
    """Devuelve el payload; lanza jwt.PyJWTError si es inválido o expiró."""
    return jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITMO])
