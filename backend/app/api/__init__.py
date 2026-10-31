from fastapi import APIRouter

from app.api import (
    auth,
    demo,
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

for modulo in (health, auth, usuarios, vehiculos, placas, disponibilidad, rentas, recibir, metricas, demo):
    api_router.include_router(modulo.router)
