from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.deps import AdminUser, DbSession
from app.services.metricas import calcular
from app.services.vencimientos import dep_sincronizar
from app.timeutil import now_utc

router = APIRouter(tags=["metricas"], dependencies=[Depends(dep_sincronizar)])


@router.get("/metricas")
def metricas(
    _: AdminUser,
    db: DbSession,
    meses: Annotated[int, Query(ge=1, le=24)] = 12,
):
    return calcular(db, now_utc(), meses)
