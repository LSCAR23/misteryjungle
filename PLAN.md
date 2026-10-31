# Mistery Jungle — Plan de implementación (Demo)

App para llevar la disponibilidad de la flota de renta de Mistery Jungle (Moto Rental & Tours, Puerto Viejo, CR).
Este documento es la **fuente de verdad** para los subagentes: todo contrato (tablas, endpoints, rutas, nombres de archivo) está aquí. Si un subagente necesita algo que no está aquí, **pregunta al orquestador; no inventa**.

---

## 0. Decisiones tomadas (no re-discutir)

| Tema | Decisión |
|---|---|
| Estado / ubicación / fecha fin | Viven en **la placa** (cada placa = una unidad física). `cantidad` del vehículo = número de placas (calculado, no columna). |
| Historial | Tabla `rentas`. Una renta = una placa. Rentar N placas crea N rentas. |
| Monto de renta | **Automático por duración**: la combinación de tarifas más barata que cubre la duración (ver §4). Se guarda en la renta. |
| Fin de renta | Al pasar `fecha_hora_finalizacion` la placa pasa sola a `Disponible` con ubicación `Ubicación no actualizada` y la renta queda `vencida_sin_recibir`. La sección **Recibir** obliga a elegir ubicación. |
| Tema visual | Claro **y** oscuro con toggle. Blanco, negro y rojo Honda. Mobile first. |
| BD producción | Render Postgres (free, región Ohio). API FastAPI en Render (Docker). Front en Vercel. |
| Repo | GitHub **público** `LSCAR23/misteryjungle`. **Un commit por microtarea.** Ningún secreto en el repo. |
| Usuarios seed | Oscar, Daniel (empleado); Ivan, Fabian (admin). Contraseña = env `SEED_PASSWORD` (nunca en código). |
| Zona horaria | `America/Costa_Rica` (UTC−06:00 fijo, sin horario de verano). En BD todo es `timestamptz` (UTC). |
| Imágenes | Campo `imagen` = ruta pública `/vehiculos/<slug>.png` servida por Next (`frontend/public/vehiculos/`). Si el PNG no existe se muestra la silueta de la categoría. |

---

## 1. Arquitectura

```
misteryjungle/
├── PLAN.md  AppCore.txt  README.md  .gitignore  .env.example  docker-compose.yml  render.yaml
├── images/                       # material original (logo, fotos de precios)
├── backend/
│   ├── Dockerfile  requirements.txt  alembic.ini  pytest.ini  .dockerignore
│   ├── alembic/ env.py  versions/0001_schema.py 0002_seed_usuarios.py 0003_seed_catalogo.py 0004_mock_data.py
│   ├── app/
│   │   ├── main.py  config.py  db.py  enums.py  models.py  schemas.py  security.py  deps.py  timeutil.py
│   │   ├── services/ pricing.py  vencimientos.py  metricas.py
│   │   ├── api/ __init__.py (registra TODOS los routers)  health.py auth.py usuarios.py vehiculos.py
│   │   │        placas.py disponibilidad.py rentas.py recibir.py metricas.py
│   │   ├── seed/ catalogo.py  mock_data.py
│   │   └── scripts/ reset_demo.py
│   └── tests/ conftest.py test_pricing.py test_auth.py test_disponibilidad.py test_rentas.py test_recibir.py test_metricas.py ...
└── frontend/                     # Next.js 16 App Router + TS + Tailwind v4
    ├── next.config.ts (rewrite /api/* → BACKEND_URL)
    ├── public/ logo.png  vehiculos/<slug>.png (los pone el usuario)  vehiculos/placeholders/<categoria>.svg
    └── src/
        ├── app/ layout.tsx globals.css  login/  (app)/layout.tsx  (app)/disponibilidad/...  (app)/recibir/
        │        (app)/admin/dashboard/  (app)/admin/usuarios/  (app)/admin/vehiculos/
        ├── components/ ui/*  shell/*  vehiculos/*  rentas/*  dashboard/*
        └── lib/ api.ts types.ts auth.tsx time.ts format.ts constants.ts
```

- **Local:** `docker compose up` levanta `db` (postgres:16-alpine, puerto host **5433**) y `api` (puerto **8000**; al arrancar corre `alembic upgrade head`). El front corre con `npm run dev` (puerto 3000).
- **Front → API:** el navegador siempre llama a `/api/...` del mismo dominio; `next.config.ts` hace `rewrites` a `${BACKEND_URL}/api/...`. Así no hay CORS en producción (igual se configura CORS en la API por seguridad: `CORS_ORIGINS`).
- **Auth:** JWT (HS256, 12 h) en `Authorization: Bearer`. El front lo guarda en `localStorage` (`mj_token`). La API valida rol en cada endpoint; el front sólo oculta UI.
- **Vencimientos sin cron:** antes de responder cualquier endpoint de disponibilidad / rentas / recibir / métricas se ejecuta `sincronizar_vencidas(db)` (dependencia FastAPI). Render free duerme, así que no dependemos de jobs.

### Stack backend
Python 3.12, FastAPI, SQLAlchemy 2.0 (ORM, sync), psycopg 3 (`psycopg[binary]`), Alembic, Pydantic v2 + pydantic-settings, `bcrypt` (directo, **no passlib**), PyJWT, `tzdata`, uvicorn. Tests: pytest + httpx (`TestClient`) contra la BD `misteryjungle_test` del compose.
`config.py` normaliza `DATABASE_URL`: si empieza con `postgres://` o `postgresql://` lo cambia a `postgresql+psycopg://` (Render entrega `postgresql://`).

### Stack frontend
Next.js 16 (App Router, `src/`), React 19, TypeScript estricto, Tailwind CSS v4, `next-themes` (toggle claro/oscuro, clase `dark`), `lucide-react` (iconos), `recharts` (gráficos), `swr` (fetch + revalidación), `sonner` (toasts). Fuentes con `next/font/google`: **Barlow Condensed** (600/700, títulos, estilo racing) y **DM Sans** (texto).

### Variables de entorno
| Var | Dónde | Ejemplo (.env.example) |
|---|---|---|
| `DATABASE_URL` | api | `postgresql+psycopg://mj:mj@db:5432/misteryjungle` |
| `TEST_DATABASE_URL` | tests | `postgresql+psycopg://mj:mj@localhost:5433/misteryjungle_test` |
| `JWT_SECRET` | api | `change-me` |
| `SEED_PASSWORD` | api (migración 0002) | `change-me` |
| `SEED_MOCK_DATA` | api (migración 0004) | `true` |
| `CORS_ORIGINS` | api | `http://localhost:3000` (coma-separado) |
| `BACKEND_URL` | front (server) | `http://localhost:8000` |

`.env` real **no se commitea**. El orquestador crea `.env` local con `SEED_PASSWORD=password` (valor pedido por el usuario).

---

## 2. Modelo de datos

Enums se guardan como `VARCHAR` + `CHECK` (SQLAlchemy `Enum(..., native_enum=False, values_callable=lambda e: [x.value for x in e], length=40)`). Los **valores** (strings) son exactamente estos:

- `Categoria`: `Scooter`, `Moto`, `ATV`, `UTV`, `Camion`
- `Ubicacion`: `Playa Chiquita`, `Puerto Viejo`, `Playa Negra`, `B.Azul`, `Taller Nico`, `Ubicación no actualizada`
  (las 5 primeras son "reales"; la última sólo la pone el sistema y **no** aparece en selects)
- `EstadoPlaca`: `Rentada`, `Disponible`, `Fuera de Servicio`
- `Rol`: `admin`, `empleado`
- `Tarifa` (código → etiqueta → horas): `5H`→"5 horas"→5 · `DIA`→"Día (8am–5:30pm)"→especial · `24H`→"24 horas"→24 · `2D`→"2 días"→48 · `3D`→"3 días"→72 · `1S`→"1 semana"→168 · `10D`→"10 días"→240 · `MES`→"Mes"→720
- `EstadoRenta`: `activa`, `vencida_sin_recibir`, `finalizada`

### Tablas
**usuarios** — `id` uuid PK · `username` varchar(50) NOT NULL · `password_hash` varchar(100) NOT NULL · `rol` Rol NOT NULL · `activo` bool default true · `created_at` timestamptz default now(). Índice único `lower(username)`.

**vehiculos** — `id` uuid PK · `marca` varchar(50) · `modelo` varchar(80) · `slug` varchar(100) UNIQUE · `imagen` varchar(255) NULL (ej. `/vehiculos/honda-navi.png`) · `cilindrada` int (>0) · `categoria` Categoria · `created_at`.

**precios** — `id` uuid PK · `vehiculo_id` FK→vehiculos ON DELETE CASCADE · `tarifa` Tarifa · `monto` numeric(10,2) (>0). UNIQUE(`vehiculo_id`,`tarifa`). Si una tarifa no existe para el vehículo, simplemente no hay fila.

**placas** — `id` uuid PK · `placa` varchar(20) NOT NULL default `'NUEVA'` · `vehiculo_id` FK→vehiculos ON DELETE CASCADE · `estado` EstadoPlaca default `Disponible` · `ubicacion_actual` Ubicacion default `Taller Nico` · `fecha_hora_finalizacion` timestamptz NULL · `created_at`.
`CHECK ((estado = 'Rentada') = (fecha_hora_finalizacion IS NOT NULL))`. Índice único parcial `upper(placa) WHERE upper(placa) <> 'NUEVA'`.

**rentas** — `id` uuid PK · `placa_id` FK→placas · `vehiculo_id` FK→vehiculos (denormalizado para métricas) · `usuario_id` FK→usuarios (quién rentó) · `inicio` timestamptz · `fin_programado` timestamptz · `fin_real` timestamptz NULL · `monto` numeric(10,2) · `desglose` varchar(120) (ej. "1 semana + 2 días") · `estado` EstadoRenta default `activa` · `ubicacion_recibida` Ubicacion NULL · `recibida_por` FK→usuarios NULL · `recibida_en` timestamptz NULL · `created_at`. Índices: (`estado`), (`fin_programado`), (`inicio`).

### Reglas de negocio
1. Rentar: todas las placas pedidas deben estar `Disponible` (bloquear con `SELECT … FOR UPDATE`); si alguna no lo está → 409 y no se crea nada. `inicio = now()`, `fin > inicio + 15 min`, `fin ≤ inicio + 90 días`. Placa → `Rentada`, `fecha_hora_finalizacion = fin`. Ubicación de la placa no cambia.
2. `sincronizar_vencidas(db, now)`: placas `Rentada` con `fecha_hora_finalizacion ≤ now` → `Disponible`, `fecha=NULL`, `ubicacion_actual='Ubicación no actualizada'`; sus rentas `activa` → `vencida_sin_recibir`, `fin_real = fin_programado`. Idempotente.
3. Recibir (cualquier rol) una renta `activa` o `vencida_sin_recibir` con una ubicación real: renta → `finalizada`, `ubicacion_recibida`, `recibida_por`, `recibida_en=now`; si era `activa` (devolución anticipada) `fin_real=now` (el monto **no** cambia). La placa recibe la ubicación y, si sigue `Rentada` **por esta misma renta**, pasa a `Disponible` con fecha NULL. Si la placa ya tiene otra renta `activa` más nueva, sólo se cierra la renta vieja y no se toca la placa.
4. Admin puede: poner `Fuera de Servicio` placas `Disponible`; `Habilitar` placas `Fuera de Servicio` (→ `Disponible`); cambiar texto de `placa` y `ubicacion_actual` de cualquier placa no rentada.
5. Una placa en `Ubicación no actualizada` **sí** se puede rentar (decisión del usuario), pero se muestra con aviso.

---

## 3. Contrato de la API (todas bajo `/api`)

Fechas: ISO 8601 con offset (la API devuelve UTC `...Z`; acepta cualquier offset). Montos: number (float con 2 decimales). Errores: `{"detail": "mensaje en español"}`. 401 sin token / token inválido, 403 rol insuficiente, 404, 409 conflicto, 422 validación.

### Tipos compartidos (espejo exacto en `frontend/src/lib/types.ts`)
```ts
type Rol = "admin" | "empleado";
type Categoria = "Scooter" | "Moto" | "ATV" | "UTV" | "Camion";
type Ubicacion = "Playa Chiquita" | "Puerto Viejo" | "Playa Negra" | "B.Azul" | "Taller Nico" | "Ubicación no actualizada";
type EstadoPlaca = "Rentada" | "Disponible" | "Fuera de Servicio";
type TarifaCodigo = "5H" | "DIA" | "24H" | "2D" | "3D" | "1S" | "10D" | "MES";
type EstadoRenta = "activa" | "vencida_sin_recibir" | "finalizada";

interface Usuario { id: string; username: string; rol: Rol; activo: boolean; created_at: string }
interface Precio { tarifa: TarifaCodigo; monto: number }
interface Placa { id: string; placa: string; vehiculo_id: string; estado: EstadoPlaca;
  ubicacion_actual: Ubicacion; fecha_hora_finalizacion: string | null }
interface Vehiculo { id: string; marca: string; modelo: string; slug: string; imagen: string | null;
  cilindrada: number; categoria: Categoria; cantidad: number; precios: Precio[] }
interface VehiculoDetalle extends Vehiculo { placas: Placa[] }
interface CategoriaResumen { categoria: Categoria; disponibles: number; total: number }
interface VehiculoDisponibilidad extends Vehiculo { disponibles: number;
  por_ubicacion: { ubicacion: Ubicacion; disponibles: number }[] }   // sólo ubicaciones con >0, orden desc
interface Cotizacion { placa_id: string; vehiculo: string; placa: string; monto: number; desglose: string }
interface CotizacionResp { inicio: string; fin: string; items: Cotizacion[]; total: number }
interface Renta { id: string; placa_id: string; placa: string; vehiculo_id: string; vehiculo: string;
  categoria: Categoria; usuario: string; inicio: string; fin_programado: string; fin_real: string | null;
  monto: number; desglose: string; estado: EstadoRenta; ubicacion_placa: Ubicacion }
```
`vehiculo` (string) en Cotizacion/Renta = `"{marca} {modelo}"`.

### Endpoints
| Método y ruta | Rol | Request | Response |
|---|---|---|---|
| GET `/api/health` | — | — | `{"status":"ok"}` (hace `SELECT 1`) |
| POST `/api/auth/login` | — | `{username, password}` (username case-insensitive) | `{access_token, token_type:"bearer", usuario: Usuario}`; 401 "Usuario o contraseña incorrectos" |
| GET `/api/auth/me` | any | — | `Usuario` |
| GET `/api/usuarios` | admin | — | `Usuario[]` orden username |
| POST `/api/usuarios` | admin | `{username (3-50, [A-Za-z0-9._-]), password (≥6), rol}` | 201 `Usuario`; 409 "El usuario ya existe" |
| GET `/api/vehiculos` | any | `?categoria=` opcional | `Vehiculo[]` orden categoría, marca, modelo |
| GET `/api/vehiculos/{id}` | any | — | `VehiculoDetalle` (placas orden: estado Disponible, Rentada, Fuera; luego placa) |
| POST `/api/vehiculos` | admin | `{marca, modelo, cilindrada, categoria, imagen?: string\|null, precios: Precio[] (≥1), placas: {placa?: string, ubicacion_actual: Ubicacion}[] (≥1)}` — slug se genera `slugify(marca-modelo)` (sufijo -2, -3 si existe); si `imagen` viene vacío se pone `/vehiculos/{slug}.png` | 201 `VehiculoDetalle` |
| POST `/api/vehiculos/{id}/placas` | admin | `{placa?: string, ubicacion_actual}` | 201 `Placa` |
| PATCH `/api/placas/{id}` | admin | `{placa?: string, ubicacion_actual?: Ubicacion}` (no se permite `Ubicación no actualizada`; 409 si la placa está Rentada y se cambia ubicación) | `Placa` |
| POST `/api/placas/estado` | admin | `{placa_ids: string[], accion: "fuera_servicio" \| "habilitar"}` (fuera_servicio exige todas Disponible; habilitar exige todas Fuera de Servicio; si no → 409 sin cambios) | `Placa[]` |
| GET `/api/disponibilidad/categorias` | any | — | `CategoriaResumen[]` (las 5 categorías siempre, en el orden del enum; `total` excluye nada) |
| GET `/api/disponibilidad?categoria=X` | any | — | `VehiculoDisponibilidad[]` (todos los vehículos de la categoría, también con 0 disponibles, orden disponibles desc) |
| POST `/api/rentas/cotizar` | any | `{placa_ids: string[] (≥1), fin: string}` | `CotizacionResp` (no valida estado, sólo fechas) |
| POST `/api/rentas` | any | `{placa_ids, fin}` | 201 `Renta[]`; 409 "Una o más placas ya no están disponibles" |
| GET `/api/rentas/activas` | any | — | `Renta[]` estado `activa`, orden fin_programado |
| GET `/api/recibir` | any | — | `{vencidas: Renta[], hoy: Renta[], sin_ubicacion: Placa&{vehiculo:string}[]}` — `vencidas` = estado `vencida_sin_recibir`; `hoy` = `activa` con fin_programado dentro del día CR de hoy; `sin_ubicacion` = placas con ubicación `Ubicación no actualizada` sin renta vencida pendiente |
| POST `/api/recibir` | any | `{renta_ids?: string[], placa_ids?: string[], ubicacion: Ubicacion real}` (`placa_ids` es para las de `sin_ubicacion`: sólo actualiza ubicación) | `{rentas_finalizadas: number, placas_actualizadas: number}` |
| GET `/api/metricas?meses=12` | admin | — | ver abajo |

**Métricas** (todas las rentas, cualquier estado; rango = últimos `meses` meses calendario CR incluyendo el actual):
```json
{
  "kpis": {
    "ingresos_mes_actual": 0, "ingresos_mes_anterior": 0, "rentas_mes_actual": 0,
    "ocupacion_actual": 0.0,           // Rentada / (total - Fuera de Servicio), 0..1
    "unidades_total": 48, "unidades_rentadas": 0, "unidades_fuera_servicio": 0,
    "pendientes_recibir": 0,           // vencida_sin_recibir + placas "Ubicación no actualizada"
    "duracion_promedio_horas": 0.0, "ticket_promedio": 0.0
  },
  "vehiculo_mas_popular": {"vehiculo": "Honda Navi", "rentas": 0},
  "vehiculo_mas_ingresos": {"vehiculo": "Honda Pioneer 4x4", "ingresos": 0},
  "usuario_top": {"usuario": "Oscar", "rentas": 0, "ingresos": 0},
  "mes_top": {"mes": "2026-03", "rentas": 0, "ingresos": 0},
  "por_mes": [{"mes": "2025-11", "rentas": 0, "ingresos": 0}],          // todos los meses del rango, también en 0
  "por_vehiculo": [{"vehiculo": "...", "categoria": "Moto", "rentas": 0, "ingresos": 0}],   // orden ingresos desc
  "por_categoria": [{"categoria": "Moto", "rentas": 0, "ingresos": 0}],
  "por_usuario": [{"usuario": "Oscar", "rentas": 0, "ingresos": 0}],
  "por_dia_semana": [{"dia": "Lun", "rentas": 0}],                      // Lun..Dom, fecha de inicio en CR
  "disponibles_por_ubicacion": [{"ubicacion": "Puerto Viejo", "disponibles": 0}]
}
```
Campos `*_top`/`*_mas_*` son `null` si no hay rentas.

---

## 4. Algoritmo de precio (`backend/app/services/pricing.py`, función pura)

```
def cotizar(precios: dict[str, Decimal], inicio: datetime, fin: datetime) -> tuple[Decimal, str]
```
1. `minutos = ceil((fin - inicio) / 1 min)`; tolerancia de 15 min: `horas = max(1, ceil((minutos - 15) / 60))`.
2. Tarifas por horas disponibles para el vehículo: `5H=5, 24H=24, 2D=48, 3D=72, 1S=168, 10D=240, MES=720`.
3. DP de mochila no acotada: `costo[0]=0`; `costo[h] = min_t( costo[max(0, h - horas_t)] + precio_t )` para `h=1..horas`. Reconstruir conteos por tarifa.
4. Candidato `DIA` (si el vehículo lo tiene): inicio y fin en el **mismo día calendario CR** y fin ≤ 17:30 CR → candidato = precio `DIA`. Total = mínimo entre DP y DIA (empate → DIA).
5. `desglose`: conteos de mayor a menor duración, etiquetas en español con plural: `"1 semana + 2 días"`, `"2 × 24 horas"`, `"Día (8am–5:30pm)"`. Formato exacto: piezas unidas por `" + "`; pieza = etiqueta si cantidad 1, si no `"{n} × {etiqueta}"`.

**Tests obligatorios** (`tests/test_pricing.py`, precios del seed):
| Vehículo | Inicio → fin (CR) | Monto esperado | Por qué |
|---|---|---|---|
| Navi | 10:00 → 14:00 | 20 | 5H |
| Navi | 08:30 → 17:00 mismo día | 30 | DIA < 24H(35) |
| Navi | 18:00 → 22:00 | 20 | 5H (DIA no aplica después de 17:30 pero 5H es más barato igual) |
| Navi | 10:00 → +29 h | 55 | 24H + 5H (< 2D 60) |
| Navi | 10:00 → +30 h | 60 | 2D (24H+5H no cubre 30 h; 24H+2×5H = 75) |
| Navi | 10:00 → +7 días | 175 | 1S |
| Navi | 10:00 → +5 h 10 min | 20 | tolerancia 15 min |
| Talon 4x4 | 10:00 → 13:00 | 250 | sólo existe 24H |
| Camión | → +30 días | 3000 | 3 × 10D (no tiene MES) |
| CRF300 Rally | 09:00 → 12:00 | 50 | DIA (no tiene 5H; 24H=80) |
| TRX | 10:00 → +12 días | 755 | 10D(600) + 2D(155); alternativas: 10D+2×24H=760, 1S+3D+2D=870, MES=1300 |

---

## 5. Catálogo seed (migración 0003, datos en `backend/app/seed/catalogo.py`)

Marca de todos = `Honda` salvo el camión (`Isuzu`). Cilindradas tomadas de fichas oficiales del modelo más probable (verificables después; editar en `catalogo.py`). Placas iniciales: todas `NUEVA`, ubicación repartida en round-robin entre `Puerto Viejo, Playa Chiquita, Playa Negra, B.Azul` (la 0004 luego cambia algunas).

| slug | modelo | cat | cc | uds | DIA | 5H | 24H | 2D | 3D | 1S | 10D | MES |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| honda-navi | Navi | Scooter | 109 | 6 | 30 | 20 | 35 | 60 | 80 | 175 | 200 | 500 |
| honda-elite | Elite 125 | Scooter | 124 | 4 | 30 | 20 | 35 | 60 | 80 | 175 | 200 | 500 |
| honda-cbf150s | CBF150S | Moto | 149 | 2 | 40 | 30 | 50 | 90 | 130 | 250 | 300 | 600 |
| honda-xr190 | XR190 | Moto | 184 | 4 | 40 | 30 | 50 | 90 | 130 | 250 | 300 | 600 |
| honda-crf250 | CRF250 | Moto | 250 | 3 | 50 | 40 | 70 | 130 | 190 | 350 | 450 | 1000 |
| honda-crf300-rally | CRF300 Rally | Moto | 286 | 4 | 50 | — | 80 | 140 | 200 | 360 | 460 | 1100 |
| honda-trx-4x4 | TRX 420 4x4 | ATV | 420 | 4 | 60 | 50 | 80 | 155 | 225 | 490 | 600 | 1300 |
| honda-rincon-4x4 | Rincon 4x4 | ATV | 675 | 6 | 80 | — | 100 | 180 | 240 | 520 | 700 | 1500 |
| honda-pioneer-4x4 | Pioneer 4x4 | UTV | 675 | 5 | 150 | — | 200 | 350 | 450 | 850 | 1000 | 2500 |
| honda-pioneer-deluxe-crew | Pioneer Deluxe Crew | UTV | 999 | 3 | 150 | — | 200 | 350 | 450 | 850 | 1000 | 2500 |
| honda-talon-4x4 | Talon 4x4 | UTV | 999 | 4 | — | — | 250 | 400 | 500 | 900 | 1100 | 2700 |
| honda-talon-4wd | Talon 4WD (4 plazas) | UTV | 999 | 2 | — | — | 300 | 500 | 600 | 1000 | 1200 | 2800 |
| isuzu-serie-q | Serie Q | Camion | 5193 | 1 | 150 | 100 | 200 | 300 | 450 | 850 | 1000 | — |

Total: 13 vehículos, **48 placas**. `imagen = /vehiculos/{slug}.png`.

## 6. Mock data (migración 0004 → `app/seed/mock_data.py: generar(conn, now)`)

Sólo SQL Core (`sa.text`), **sin importar modelos ORM**. Se salta si `SEED_MOCK_DATA` == `false`. `random.Random(2310)` para que sea determinista. Usuario `rentado_por` ponderado: Oscar 35 %, Daniel 30 %, Ivan 20 %, Fabian 15 %.

1. **Placas reales**: a 20 placas (las primeras de cada vehículo en orden) se les asigna número: motos/scooters/ATV/UTV `MOT 5xxxxx`, camión `CL 2xxxxx` (6 dígitos aleatorios, únicos). El resto queda `NUEVA`.
2. **Historial** (~220 rentas `finalizada`) en los últimos 12 meses (no en el futuro): peso por mes temporada alta CR (dic–abr ×1.6, jul ×1.3, sep–oct ×0.7, resto ×1.0); vehículo ponderado (scooters ×3, motos ×2, ATV ×1.5, UTV ×1, camión ×0.3). Tarifa elegida al azar entre las del vehículo (pesos: 5H 2, DIA 3, 24H 4, 2D 3, 3D 2, 1S 1.5, 10D 0.5, MES 0.2), `fin = inicio + horas tarifa` (DIA = 08:30→17:00 CR), `monto` = precio de esa tarifa, `desglose` = etiqueta. `inicio` hora aleatoria 7:00–16:00 CR. `ubicacion_recibida` aleatoria real; `recibida_por` = mismo usuario.
3. **Estado actual** (relativo a `now`):
   - 12 placas `Rentada` con renta `activa` (inicio entre hace 2 días y hace 1 h): 4 terminan **hoy** (entre now+1h y 17:30 CR; si ya pasó 15:30 CR, entre now+1h y now+3h), 8 terminan entre mañana y +6 días.
   - 2 rentas `vencida_sin_recibir` (fin ayer) → su placa `Disponible` + `Ubicación no actualizada`.
   - 3 placas `Fuera de Servicio` en `Taller Nico`.
   - El resto `Disponible` en ubicaciones reales variadas.
   - Las placas elegidas para cada grupo nunca se repiten; incluir al menos una Navi, una Talon y el camión entre las rentadas.
4. `app/scripts/reset_demo.py`: `python -m app.scripts.reset_demo` borra rentas, resetea placas a `NUEVA`/Disponible y vuelve a correr `generar(conn, now)`. **Se corre la mañana de la demo** para que "hoy" sea hoy.

---

## 7. Diseño (frontend)

- **Tokens** (en `globals.css` con `@theme` + variables por tema; `@custom-variant dark (&:where(.dark, .dark *));`):
  - Claro: `--bg #FFFFFF`, `--surface #F5F5F5`, `--surface-2 #EBEBEB`, `--ink #0A0A0A`, `--ink-muted #5C5C5C`, `--border #E2E2E2`, `--red #CC0000`, `--red-hover #A80000`, `--red-soft #FDECEC`.
  - Oscuro: `--bg #0A0A0A`, `--surface #151515`, `--surface-2 #1F1F1F`, `--ink #F5F5F5`, `--ink-muted #A3A3A3`, `--border #2A2A2A`, `--red #E10600`, `--red-hover #FF2A1F`, `--red-soft #2A0B0A`.
  - Semánticos (sólo puntos/badges): Disponible `#16A34A`, Rentada = rojo marca, Fuera de servicio `#737373`, Ubicación no actualizada `#D97706`.
- **Tipografía:** títulos Barlow Condensed 700 uppercase con tracking leve; texto DM Sans. Números con `tabular-nums`.
- **Layout mobile first** (base = 360–430 px): header fijo con logo (32 px) + nombre + toggle tema; **bottom nav** fija (Disponibilidad, Recibir, y para admin Dashboard y Más→Usuarios/Vehículos). `md:` (≥768) grids de 2–3 columnas; `lg:` (≥1024) sidebar izquierda en vez de bottom nav. Contenido `max-w-6xl`. Áreas táctiles ≥ 44 px. `pb-[calc(env(safe-area-inset-bottom)+72px)]` para no tapar con la nav.
- **Estilo:** tarjetas con radio 16 px, borde 1 px `--border`, sombra muy suave en claro; franja/acento rojo diagonal en headers de sección (guiño a la gráfica de los volantes). Botón primario rojo, secundario negro (claro) / blanco (oscuro). Skeletons en cargas, empty states con icono, toasts `sonner`. Transiciones 150–200 ms sólo de `opacity/transform`.
- **Imagen de vehículo:** componente `VehicleImage` → `<img src={imagen}>` con `onError` a `/vehiculos/placeholders/{categoria}.svg` (siluetas simples monocromas: scooter, moto, atv, utv, camion). Fondo de la tarjeta degradado gris claro para que los PNG sin fondo luzcan.
- Logo: copiar `images/Mistery-Jungle-Logo.png` → `frontend/public/logo.png` y generar `src/app/icon.png` (favicon) del mismo.

### Pantallas
1. **/login** — logo grande centrado, usuario + contraseña, botón rojo "Entrar". Error inline. Redirige: admin → `/admin/dashboard`, empleado → `/disponibilidad`.
2. **/disponibilidad** — grid de 5 tarjetas de categoría (icono silueta, nombre, "12 de 14 disponibles", barra de progreso).
3. **/disponibilidad/[categoria]** — lista de vehículos (imagen, nombre, cc, chip "X disponibles") y debajo chips por ubicación `Puerto Viejo · 3`. Vehículos con 0 disponibles al final, atenuados.
4. **/disponibilidad/[categoria]/[vehiculoId]** — cabecera del vehículo + tabla de precios plegable. Filtro por ubicación (chips). Lista de placas como tarjetas seleccionables (checkbox grande): placa (o "NUEVA · últimos 4 del id"), ubicación (ámbar si no actualizada), estado. Rentadas se muestran atenuadas con "Vuelve: vie 31 oct, 5:30 pm" y no se seleccionan. **Empleado** ve y selecciona sólo Disponibles. **Admin** ve todas; puede seleccionar Disponibles o Fuera de Servicio (no mezclar: al tocar una de otro estado se limpia la selección previa con toast). Admin además ve icono lápiz por placa → sheet para editar texto de placa y ubicación. Botón "Seleccionar todas".
   **Barra de acción fija** (arriba de la bottom nav) cuando hay selección: "N seleccionadas" + `Rentar` (si son Disponibles) + `Fuera de servicio` (admin, si Disponibles) / `Habilitar` (admin, si Fuera de Servicio).
5. **Sheet "Rentar"** (bottom sheet en móvil, modal centrado en desktop): inicio = "Ahora (hora CR)" de sólo lectura; fin con `<input type="datetime-local">` + chips rápidos `+5 h`, `Hoy 5:30 pm`, `+24 h`, `+3 días`, `+1 semana`. Al cambiar fin → `POST /rentas/cotizar` (debounce 300 ms) y muestra por placa monto + desglose y total grande. Botón "Confirmar renta · $X". Éxito → toast + volver a la lista (SWR revalida). 409 → toast de error y revalidar.
6. **/recibir** — 3 secciones: "Vencidas sin recibir" (borde ámbar), "Vencen hoy", "Ubicación no actualizada". Cada ítem: vehículo, placa, quién rentó, hora fin. Selección múltiple + barra "Recibir en…" → sheet con las 5 ubicaciones como botones grandes. Badge con conteo de pendientes en el ítem "Recibir" de la nav.
7. **/admin/dashboard** — fila de KPIs (2 col móvil, 4 desktop): ingresos mes (vs anterior ↑↓ %), rentas mes, ocupación %, pendientes por recibir (link a /recibir). Tarjetas "destacados": vehículo más popular, vehículo que más deja, usuario top, mejor mes. Gráficos (recharts, color rojo marca, un solo color + grises): ingresos por mes (barras), ingresos por vehículo (barras horizontales top 8), rentas por categoría (barras), rentas por día de semana (barras), disponibles por ubicación (barras). Formato moneda `$1,234` (USD, `Intl` en-US).
8. **/admin/usuarios** — lista (username, rol badge) + botón "Nuevo usuario" → `/admin/usuarios/nuevo` (form: usuario, contraseña con mostrar/ocultar, rol segmentado Empleado/Admin).
9. **/admin/vehiculos** — lista agrupada por categoría (imagen, nombre, cc, cantidad) → detalle reutiliza la pantalla 4. "Nuevo vehículo" → `/admin/vehiculos/nuevo`: marca, modelo, cilindrada, categoría (segmentado), imagen (texto opcional con ayuda "deja vacío para usar /vehiculos/{slug}.png"), precios (8 filas tarifa + input opcional; ≥1 requerido), placas: stepper de cantidad + lista editable (placa opcional → "NUEVA", ubicación select).

Guardas: `(app)/layout.tsx` es cliente: sin token → `/login`; rutas `/admin/*` con rol empleado → `/disponibilidad`. 401 de la API en cualquier fetch → borrar token y `/login`.

Utilidades de tiempo (`lib/time.ts`): CR es UTC−6 fijo. `crInputToISO("2026-10-31T17:30") → "2026-10-31T17:30:00-06:00"`; `isoToCrInput(iso)`; `formatCR(iso)` con `Intl.DateTimeFormat("es-CR", {timeZone:"America/Costa_Rica", ...})`. **Nunca** usar la zona del dispositivo.

---

## 8. Reglas para subagentes y commits

- Cada subagente recibe: este PLAN.md + el ID de su microtarea. Toca **sólo** los archivos listados en su tarea (si necesita otro, lo reporta).
- Los subagentes **no hacen commit ni push** (en paralelo se pisarían el índice de git). Al terminar reportan: archivos cambiados, comandos de verificación corridos y su salida resumida.
- El **orquestador** revisa, corre la verificación, y hace **un commit por microtarea** con el mensaje indicado (Conventional Commits en español) + `Co-Authored-By`. Push al final de cada fase.
- Para evitar conflictos en archivos compartidos: B1 crea `app/api/__init__.py` registrando todos los routers y cada `app/api/<x>.py` como stub `router = APIRouter()`; F1 crea las carpetas de rutas con `page.tsx` placeholder. Así cada tarea paralela edita sólo su archivo.
- Modelo sugerido por tarea: **H** = Haiku (mecánico, datos, boilerplate), **S** = Sonnet (lógica, UI con criterio). El orquestador (Opus) hace F0, revisión, integración y deploy.
- Definición de "hecho" de toda tarea backend: `docker compose exec api pytest -q` verde. De toda tarea frontend: `npm run lint && npx tsc --noEmit && npm run build` verde.

---

## 9. Fases y microtareas

Leyenda: `‖` = en paralelo dentro de la ola. Cada ola empieza cuando la anterior está commiteada.

### FASE 0 — Base del repo (orquestador, secuencial)
- **F0.1** `.gitignore` (Python, Node, `.env`, `.next`, `__pycache__`, `node_modules`, `.venv`), `.env.example`, `README.md` (qué es, cómo correr), `PLAN.md`, `AppCore.txt`, `images/`. Crear repo público `LSCAR23/misteryjungle` y push. — commit `chore: estructura inicial, plan e imágenes`

### FASE 1 — Cimientos (Ola 1: B1 ‖ P1 ‖ F1 ‖ A1)
- **B1 (S)** Esqueleto backend + Docker. Archivos: `backend/requirements.txt`, `backend/Dockerfile` (python:3.12-slim, usuario no root, `CMD sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"`), `backend/.dockerignore`, `app/main.py` (FastAPI, CORS desde `CORS_ORIGINS`, incluye `api_router`), `app/config.py` (pydantic-settings + normalización de URL), `app/db.py` (engine, `SessionLocal`, `get_db`), `app/api/__init__.py` + stubs de todos los routers, `app/api/health.py` real, `docker-compose.yml` (db con healthcheck + `docker/initdb/01-test-db.sql` que crea `misteryjungle_test`; api depende de db healthy; volumen `pgdata`; `env_file: .env`), `pytest.ini`, `tests/conftest.py` (engine de test, crea/limpia esquema con `alembic upgrade head` sobre TEST_DATABASE_URL, fixture `client`), `tests/test_health.py`. Hecho: `docker compose up -d --build` y `curl localhost:8000/api/health` → ok. — commit `feat(api): esqueleto FastAPI, docker compose y healthcheck`
- **P1 (S)** `app/services/pricing.py` + `app/enums.py` (todos los enums de §2 con etiquetas y horas de Tarifa) + `tests/test_pricing.py` (tabla de §4; corre sin BD: `pytest tests/test_pricing.py`). — commit `feat(api): cálculo de tarifa óptima por duración`
- **F1 (S)** Scaffold frontend: `create-next-app` (TS, ESLint, Tailwind, App Router, src, alias `@/*`, sin turbopack flags raros), deps de §1, `globals.css` con tokens §7, `app/layout.tsx` (fuentes, `ThemeProvider` next-themes `attribute="class"`, `Toaster`), `next.config.ts` con rewrites, copiar logo + `icon.png`, carpetas de rutas de §7 con `page.tsx` placeholder, `lib/constants.ts` (listas de categorías, ubicaciones reales, etiquetas de tarifa). — commit `feat(web): scaffold Next.js, tema claro/oscuro y rutas`
- **A1 (H)** `frontend/public/vehiculos/placeholders/{Scooter,Moto,ATV,UTV,Camion}.svg` (siluetas lado izquierdo→derecho, `currentColor` no: usar `#9A9A9A`, viewBox 0 0 240 140) + `frontend/public/vehiculos/README.md` (lista de los 13 nombres de archivo esperados, PNG sin fondo, ~1200×800, orientados hacia la derecha). — commit `feat(web): siluetas por categoría y guía de imágenes`

### FASE 2 — Datos (Ola 2: B2 → (B3 ‖ B4 ‖ B5) ; en paralelo F2 ‖ F3)
- **B2 (S)** `app/models.py` (ORM de §2, usa `app/enums.py`) + `alembic.ini`, `alembic/env.py` (lee URL de config), `versions/0001_schema.py` escrita a mano (revision `"0001"`, down `None`) con CHECKs e índices de §2. Hecho: migración sube y baja limpio. — commit `feat(api): modelos y migración del esquema`
- **B3 (H)** `versions/0002_seed_usuarios.py` (rev `"0002"`, down `"0001"`): 4 usuarios, hash bcrypt de `os.environ["SEED_PASSWORD"]` (falla con mensaje claro si falta). Downgrade borra esos 4. — commit `feat(api): migración de usuarios iniciales`
- **B4 (H)** `app/seed/catalogo.py` (tabla §5 como lista de dicts) + `versions/0003_seed_catalogo.py` (rev `"0003"`, down `"0002"`). Test `tests/test_seed.py`: 13 vehículos, 48 placas, Talon 4x4 sin DIA/5H, camión sin MES. — commit `feat(api): migración del catálogo de vehículos, precios y placas`
- **B5 (S)** `app/seed/mock_data.py` + `versions/0004_mock_data.py` (rev `"0004"`, down `"0003"`) + `app/scripts/reset_demo.py` según §6. Test: tras migrar hay 12 Rentadas, 3 Fuera, 2 vencidas, CHECK de §2 se cumple, ninguna placa con 2 rentas activas. — commit `feat(api): mock data para demo y script reset_demo`
- **F2 (S)** `lib/types.ts` (espejo §3), `lib/api.ts` (`apiFetch<T>(path, {method, body})` con token, manejo de 401 y `detail`), `lib/auth.tsx` (AuthProvider: login/logout/usuario, persistencia `mj_token` + `mj_user`), `lib/time.ts`, `lib/format.ts` (moneda, fechas CR, "NUEVA · abcd"), `app/login/page.tsx`. — commit `feat(web): cliente API, sesión y pantalla de login`
- **F3 (S)** Primitivos `components/ui/`: Button (primary/secondary/ghost/danger, loading), Card, Badge, EstadoBadge, UbicacionChip, Sheet (bottom sheet móvil / modal desktop, focus trap, Esc, bloquear scroll), Skeleton, EmptyState, SegmentedControl, Input/Select/Label, Checkbox grande, `components/vehiculos/VehicleImage.tsx`, `components/shell/ThemeToggle.tsx`. — commit `feat(web): componentes base de UI`

### FASE 3 — Lógica API ‖ Shell web (Ola 3: B6 ‖ B7 ‖ F4)
- **B6 (S)** `app/security.py` (bcrypt, JWT), `app/deps.py` (`get_current_user`, `require_admin`, `sync_vencidas` dependency), `app/api/auth.py`, `app/api/usuarios.py`, `tests/test_auth.py` (login ok/mal, case-insensitive, me, 403 empleado en /usuarios, crear duplicado 409). Fixture `token(rol)` en conftest. — commit `feat(api): autenticación JWT y gestión de usuarios`
- **B7 (S)** `app/timeutil.py` (`now_utc()`, `CR = ZoneInfo("America/Costa_Rica")`, `inicio_fin_dia_cr(now)`), `app/services/vencimientos.py` (`sincronizar_vencidas`), `tests/test_vencimientos.py` (usa `now` inyectado). — commit `feat(api): vencimiento automático de rentas`
- **F4 (S)** `app/(app)/layout.tsx` (guardas), `components/shell/` Header, BottomNav, Sidebar (lg), badge de pendientes (consulta `/api/recibir` cada 60 s vía SWR), logout. — commit `feat(web): navegación responsive y guardas por rol`

### FASE 4 — Endpoints (Ola 4: B8 ‖ B9 ‖ B10 ‖ B11 ‖ B12) — cada uno sólo su router + su test
- **B8 (S)** `api/vehiculos.py` + `api/placas.py` + schemas en `app/schemas.py` (sección marcada `# --- vehiculos/placas ---`) + `tests/test_vehiculos.py`. — commit `feat(api): endpoints de vehículos y placas`
- **B9 (S)** `api/disponibilidad.py` + `tests/test_disponibilidad.py`. — commit `feat(api): endpoints de disponibilidad`
- **B10 (S)** `api/rentas.py` (cotizar, crear con FOR UPDATE, activas) + `tests/test_rentas.py` (409 en doble renta, monto correcto, fin inválido 422). — commit `feat(api): cotizar y crear rentas`
- **B11 (S)** `api/recibir.py` + `tests/test_recibir.py` (vencida, anticipada, placa re-rentada, sin_ubicacion). — commit `feat(api): recepción de vehículos y ubicación`
- **B12 (S)** `services/metricas.py` + `api/metricas.py` + `tests/test_metricas.py`. — commit `feat(api): métricas del dashboard`

> Para evitar choques en `app/schemas.py`, B1 lo crea con secciones vacías comentadas (`# --- auth ---`, `# --- vehiculos/placas ---`, `# --- disponibilidad ---`, `# --- rentas ---`, `# --- recibir ---`, `# --- metricas ---`) y cada tarea sólo escribe en la suya. Si dos tareas chocan, el orquestador resuelve al commitear.

### FASE 5 — Pantallas (Ola 5: F5 ‖ F6 ‖ F7 ‖ F8 ‖ F9 ‖ F10) — requiere API completa corriendo en docker
- **F5 (S)** Pantallas 2 y 3 (`disponibilidad/page.tsx`, `disponibilidad/[categoria]/page.tsx`, `components/vehiculos/CategoriaCard.tsx`, `VehiculoCard.tsx`). — commit `feat(web): disponibilidad por categoría y vehículo`
- **F6 (S)** Pantalla 4 (`disponibilidad/[categoria]/[vehiculoId]/page.tsx`, `components/vehiculos/PlacaCard.tsx`, `ActionBar.tsx`, `PreciosTable.tsx`, `EditarPlacaSheet.tsx`, acciones fuera de servicio/habilitar). — commit `feat(web): detalle de vehículo con selección de placas`
- **F7 (S)** Sheet de renta (`components/rentas/RentarSheet.tsx`) e integración en F6 vía prop `onRentar` (F6 deja el botón llamando `openRentar(placas)`; F7 exporta `RentarSheet` con props `{open, onClose, placas: Placa[], onDone}`). — commit `feat(web): flujo de renta con cotización en vivo`
- **F8 (S)** Pantalla 6 Recibir (`recibir/page.tsx`, `components/rentas/RecibirSheet.tsx`). — commit `feat(web): sección Recibir`
- **F9 (S)** Pantalla 7 Dashboard (`admin/dashboard/page.tsx`, `components/dashboard/*`). Cargar skill `dataviz` antes de los gráficos. — commit `feat(web): dashboard de métricas`
- **F10 (S)** Pantallas 8 y 9 (`admin/usuarios/*`, `admin/vehiculos/*`). — commit `feat(web): registro de usuarios y vehículos`

### FASE 6 — QA de integración (orquestador + 1 agente S, secuencial)
- **Q1** `docker compose down -v && up --build` desde cero; correr toda la suite pytest; `npm run build`.
- **Q2 (S)** Playwright e2e (`frontend/e2e/`) en viewport 390×844 y 1280×800: login empleado → rentar 2 Navi → aparecen rentadas → recibir; login admin → fuera de servicio/habilitar, crear usuario, crear vehículo, dashboard renderiza sin errores de consola. — commit `test(web): e2e de flujos principales`
- **Q3** Revisión visual manual con Chrome (móvil, tablet, desktop, claro/oscuro) y lista de bugs → fixes, **un commit por fix** `fix(...)`.

### FASE 7 — Deploy (orquestador, secuencial)
- **D1** `render.yaml` (Blueprint): `databases: misteryjungle-db` (free, ohio, postgres 16) + `web: misteryjungle-api` (docker, `dockerContext: ./backend`, free, ohio, `healthCheckPath: /api/health`, `DATABASE_URL fromDatabase connectionString`, `JWT_SECRET generateValue: true`, `SEED_PASSWORD`/`CORS_ORIGINS` `sync: false`, `SEED_MOCK_DATA=true`). — commit `chore(deploy): blueprint de Render`
- **D2** Añadir MCP de Render (`claude mcp add --transport http render https://mcp.render.com/mcp --header "Authorization: Bearer <RENDER_API_KEY>"` — el usuario pega su API key). Crear BD + servicio desde el MCP; si el MCP no soporta algo, el usuario abre `https://dashboard.render.com/blueprint/new?repo=https://github.com/LSCAR23/misteryjungle` (1 clic). Verificar `/api/health` y login.
- **D3** Vercel (plugin/CLI ya disponibles): proyecto con root `frontend`, env `BACKEND_URL=https://misteryjungle-api.onrender.com`, deploy a producción. Actualizar `CORS_ORIGINS` en Render con el dominio de Vercel.
- **D4** Smoke test en producción desde el celular (Chrome DevTools móvil): login de los 4 usuarios, renta, recibir, dashboard. README con URLs, usuarios demo y **checklist del día de la demo**: (1) abrir la API 5 min antes (cold start ~50 s), (2) correr `reset_demo` en el Shell de Render, (3) login de prueba. — commit `docs: URLs de producción y checklist de demo`

### Mapa de dependencias (resumen)
```
F0 → Ola1 [B1 ‖ P1 ‖ F1 ‖ A1]
   → Ola2 [B2 → (B3 ‖ B4 ‖ B5)]  ‖  [F2 ‖ F3]        (F2,F3 necesitan F1)
   → Ola3 [B6 ‖ B7 ‖ F4]                               (B6,B7 necesitan B2; F4 necesita F2,F3)
   → Ola4 [B8 ‖ B9 ‖ B10 ‖ B11 ‖ B12]                 (necesitan B6,B7; B10 necesita P1)
   → Ola5 [F5 ‖ F6 ‖ F7 ‖ F8 ‖ F9 ‖ F10]               (necesitan F4 + Ola4)
   → Fase 6 QA → Fase 7 Deploy
```
Las olas 4 (backend) y la parte de F4 pueden solaparse; las pantallas (Ola 5) se pueden empezar contra el contrato antes de que la API esté lista, pero su verificación final necesita la API.

---

## 10. Riesgos para la demo y mitigación
| Riesgo | Mitigación |
|---|---|
| Cold start de Render free (~50 s) | Abrir la app 5 min antes; pantalla de login muestra "Conectando con el servidor…" si `/api/health` tarda. |
| Datos "de hoy" viejos | `reset_demo` la mañana de la demo. |
| Zona horaria del celular distinta | Todo se convierte explícitamente a UTC−6; nunca hora local del dispositivo. |
| Doble renta simultánea | `SELECT … FOR UPDATE` + 409 + revalidación en el front. |
| Imágenes faltantes | Silueta por categoría automática. |
| Error de build en Vercel | `npm run build` obligatorio en cada tarea frontend y en Q1. |
| BD free de Render expira a 30 días | Aceptado para demo; si se aprueba, migrar a plan pago o Neon. |
