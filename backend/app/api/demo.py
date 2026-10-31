"""Herramientas de demo: reiniciar los datos de prueba (solo admin)."""
from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.deps import AdminUser, DbSession
from app.scripts.reset_demo import reiniciar
from app.timeutil import now_utc

router = APIRouter(tags=["demo"])


@router.post("/demo/reset")
def reset_demo(db: DbSession, _admin: AdminUser) -> dict:
    if not get_settings().seed_mock_data:
        raise HTTPException(status_code=403, detail="El reinicio de demo está desactivado")
    resumen = reiniciar(db.connection(), now_utc())
    db.commit()
    return resumen
