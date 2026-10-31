from fastapi import APIRouter

from app.api import (
    auth,
    disponibilidad,
    health,
    metricas,
    placas,
    recibir,
    rentas,
    usuarios,
    vehiculos,
)

api_router = APIRouter(prefix="/api")

for modulo in (health, auth, usuarios, vehiculos, placas, disponibilidad, rentas, recibir, metricas):
    api_router.include_router(modulo.router)
