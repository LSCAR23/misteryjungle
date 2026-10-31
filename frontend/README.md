# Mistery Jungle · Flota (frontend)

Next.js 16 (App Router) + React 19 + TypeScript + Tailwind CSS v4.

## Cómo correr

```bash
cp .env.example .env.local   # ajusta BACKEND_URL si hace falta
npm install
npm run dev                  # http://localhost:3000
```

La API (FastAPI) debe estar en `BACKEND_URL` (por defecto `http://localhost:8000`; ver `docker compose up` en la raíz).
El navegador siempre llama a `/api/...`; `next.config.ts` lo reescribe a `${BACKEND_URL}/api/...`.

## Verificación

```bash
npm run lint && npx tsc --noEmit && npm run build
```
