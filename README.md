# Mistery Jungle — Disponibilidad de flota

App para llevar la disponibilidad de la flota de renta de **Mistery Jungle · Moto Rental & Tours** (Puerto Viejo, Costa Rica).

| Parte | Tecnología | Producción |
|---|---|---|
| Frontend | Next.js 16 (mobile first, tema claro/oscuro) | Vercel → https://misteryjungle.vercel.app |
| API | FastAPI (Docker) | Render → https://misteryjungle-api.onrender.com |
| Base de datos | PostgreSQL | Neon (proyecto `misteryjungle`, aws-us-east-2) |

El plan completo de implementación está en [PLAN.md](PLAN.md).

## Usuarios demo

| Usuario | Rol |
|---|---|
| Ivan, Fabian | admin (dashboard, vehículos, usuarios, disponibilidad, recibir) |
| Oscar, Daniel | empleado (disponibilidad, recibir) |

La contraseña es el valor de `SEED_PASSWORD` (no está en el repo).

## Checklist el día de la demo

1. **Despertar la API** 5 minutos antes: abrir https://misteryjungle-api.onrender.com/api/health (Render free tarda ~50 s en arrancar).
2. **Reiniciar los datos de demo** para que las rentas "de hoy" sean de hoy: entrar como admin y llamar `POST /api/demo/reset`, o desde la terminal:
   ```bash
   TOKEN=$(curl -s -X POST https://misteryjungle.vercel.app/api/auth/login -H 'content-type: application/json' \
     -d '{"username":"ivan","password":"<SEED_PASSWORD>"}' | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
   curl -s -X POST https://misteryjungle.vercel.app/api/demo/reset -H "Authorization: Bearer $TOKEN"
   ```
   (Borra rentas, usuarios y vehículos creados en pruebas y regenera el historial.)
3. Login de prueba con un admin y un empleado.

## Correr en local

```bash
cp .env.example .env          # y cambia SEED_PASSWORD / JWT_SECRET
docker compose up -d --build  # BD (puerto 5433) + API (puerto 8000, recarga al guardar)
cd frontend && npm install && npm run dev   # http://localhost:3000
```

Pruebas:

```bash
docker compose exec api pytest -q                      # backend
cd frontend && E2E_PASSWORD=<pw> npm run test:e2e      # e2e (móvil + desktop)
```

## Despliegue

- **Frontend:** cada push a `main` despliega en Vercel (Root Directory = `frontend`, env `BACKEND_URL`).
- **API:** cada push a `main` despliega en Render (`render.yaml`; env `DATABASE_URL` de Neon, `SEED_PASSWORD`, `CORS_ORIGINS`). Al arrancar corre `alembic upgrade head`.
- **Imágenes de vehículos:** dejar el PNG sin fondo en `imagenes_vehiculos/` (con el modelo en el nombre) y correr `python scripts/preparar_imagenes.py`.
