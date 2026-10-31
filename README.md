# Mistery Jungle — Disponibilidad de flota

App para llevar la disponibilidad de la flota de renta de **Mistery Jungle · Moto Rental & Tours** (Puerto Viejo, Costa Rica).

- **Backend:** FastAPI + PostgreSQL (Docker) → Render
- **Frontend:** Next.js (mobile first, tema claro/oscuro) → Vercel

El plan completo de implementación está en [PLAN.md](PLAN.md).

## Correr en local

```bash
cp .env.example .env          # y cambia SEED_PASSWORD / JWT_SECRET
docker compose up -d --build  # BD (puerto 5433) + API (puerto 8000)
cd frontend && npm install && npm run dev   # http://localhost:3000
```
