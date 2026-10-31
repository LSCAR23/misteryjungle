"""Datos de demostración (PLAN §6). Sólo SQL Core; no importa los modelos ORM."""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import sqlalchemy as sa

from app.enums import TARIFA_ETIQUETA, TARIFA_HORAS
from app.services.pricing import cotizar

CR = ZoneInfo("America/Costa_Rica")
SEMILLA = 2310

UBICACIONES_REALES = ["Playa Chiquita", "Puerto Viejo", "Playa Negra", "B.Azul", "Taller Nico"]
UBICACIONES_DISPONIBLES = ["Playa Chiquita", "Puerto Viejo", "Playa Negra", "B.Azul"]
NO_ACTUALIZADA = "Ubicación no actualizada"

PESOS_USUARIO = {"oscar": 35, "daniel": 30, "ivan": 20, "fabian": 15}
PESOS_CATEGORIA = {"Scooter": 3, "Moto": 2, "ATV": 1.5, "UTV": 1, "Camion": 0.3}
PESOS_TARIFA = {"5H": 2, "DIA": 3, "24H": 4, "2D": 3, "3D": 2, "1S": 1.5, "10D": 0.5, "MES": 0.2}
HISTORICAS = 220
N_RENTADAS, N_HOY, N_VENCIDAS, N_FUERA, N_PLACAS_REALES = 12, 4, 2, 3, 20


def _peso_mes(mes: int) -> float:
    if mes in (12, 1, 2, 3, 4):
        return 1.6
    if mes == 7:
        return 1.3
    if mes in (9, 10):
        return 0.7
    return 1.0


def _cr(dia, minutos: int) -> datetime:
    """Fecha `dia` (date) a las `minutos` desde medianoche, hora de Costa Rica."""
    return datetime(dia.year, dia.month, dia.day, tzinfo=CR) + timedelta(minutes=minutos)


def generar(conn: sa.Connection, now: datetime) -> dict:
    """Genera placas reales, historial y estado actual. Requiere la tabla rentas vacía."""
    if now.tzinfo is None:
        raise ValueError("now debe incluir zona horaria")
    if conn.execute(sa.text("SELECT count(*) FROM rentas")).scalar_one() != 0:
        raise RuntimeError("La tabla rentas no está vacía; no se pueden generar datos de demo")

    rng = random.Random(SEMILLA)
    now_cr = now.astimezone(CR)

    # ---- Lectura del catálogo (orden estable) ----
    vehiculos = [
        dict(r)
        for r in conn.execute(
            sa.text("SELECT id, slug, categoria FROM vehiculos ORDER BY slug")
        ).mappings()
    ]
    precios: dict = {v["id"]: {} for v in vehiculos}
    for r in conn.execute(
        sa.text("SELECT vehiculo_id, tarifa, monto FROM precios ORDER BY vehiculo_id, tarifa")
    ).mappings():
        precios.setdefault(r["vehiculo_id"], {})[r["tarifa"]] = Decimal(r["monto"])
    orden_veh = {v["id"]: i for i, v in enumerate(vehiculos)}
    placas = [
        dict(p)
        for p in conn.execute(
            sa.text("SELECT id, vehiculo_id, placa, ubicacion_actual, created_at FROM placas")
        ).mappings()
    ]
    placas.sort(key=lambda p: (orden_veh[p["vehiculo_id"]], p["created_at"], str(p["id"])))
    if not placas:
        raise RuntimeError("No hay placas en el catálogo")
    veh_by_id = {v["id"]: v for v in vehiculos}
    por_vehiculo: dict = {v["id"]: [] for v in vehiculos}
    for i, p in enumerate(placas):
        por_vehiculo[p["vehiculo_id"]].append(i)

    usuarios = {
        r["username"].lower(): r["id"]
        for r in conn.execute(
            sa.text("SELECT id, username FROM usuarios ORDER BY lower(username)")
        ).mappings()
    }
    nombres_u = [u for u in PESOS_USUARIO if u in usuarios] or sorted(usuarios)
    if not nombres_u:
        raise RuntimeError("No hay usuarios para asignar las rentas")
    pesos_u = [PESOS_USUARIO.get(u, 1) for u in nombres_u]

    def usuario():
        return usuarios[rng.choices(nombres_u, weights=pesos_u)[0]]

    # Estado final por placa
    final = {
        i: {"placa": p["placa"], "estado": "Disponible", "ub": p["ubicacion_actual"], "fecha": None}
        for i, p in enumerate(placas)
    }
    ocupado: dict[int, list] = {i: [] for i in range(len(placas))}
    rentas: list[dict] = []

    # ---- 1. Placas reales (primeras de cada vehículo, luego segundas...) ----
    candidatas: list[int] = []
    ronda = 0
    while len(candidatas) < N_PLACAS_REALES and any(len(v) > ronda for v in por_vehiculo.values()):
        for v in vehiculos:
            idxs = por_vehiculo[v["id"]]
            if len(idxs) > ronda and len(candidatas) < N_PLACAS_REALES:
                candidatas.append(idxs[ronda])
        ronda += 1
    usadas: set[str] = {p["placa"].upper() for p in placas if p["placa"].upper() != "NUEVA"}
    for i in candidatas:
        camion = veh_by_id[placas[i]["vehiculo_id"]]["categoria"] == "Camion"
        while True:
            num = f"CL 2{rng.randint(0, 99999):05d}" if camion else f"MOT 5{rng.randint(0, 99999):05d}"
            if num not in usadas:
                usadas.add(num)
                break
        final[i]["placa"] = num

    # ---- 3. Estado actual: selección de placas por grupo ----
    def primera(pred):
        for i, p in enumerate(placas):
            if pred(veh_by_id[p["vehiculo_id"]]):
                return i
        return None

    forzadas: list[int] = []
    for pred in (
        lambda v: v["slug"] == "honda-navi",
        lambda v: v["slug"] == "honda-talon-4x4",
        lambda v: v["categoria"] == "Camion",
    ):
        i = primera(pred)
        if i is not None and i not in forzadas:
            forzadas.append(i)
    libres = [i for i in range(len(placas)) if i not in forzadas]
    rentadas = forzadas + rng.sample(libres, N_RENTADAS - len(forzadas))
    libres = [i for i in libres if i not in rentadas]
    vencidas = rng.sample(libres, N_VENCIDAS)
    libres = [i for i in libres if i not in vencidas]
    fuera = rng.sample(libres, N_FUERA)
    resto = [i for i in libres if i not in fuera]

    # Rentadas: 4 terminan hoy, el resto entre mañana y +6 días
    hoy = set(rng.sample(rentadas, N_HOY))
    fin_dia = _cr(now_cr.date(), 23 * 60 + 59)
    for i in rentadas:
        if i in hoy:
            minimo = now + timedelta(hours=1)
            if now_cr.hour * 60 + now_cr.minute >= 15 * 60 + 30:
                maximo = now + timedelta(hours=3)
            else:
                maximo = _cr(now_cr.date(), 17 * 60 + 30)
            maximo = max(min(maximo, fin_dia), minimo)
            fin = minimo + timedelta(seconds=rng.randint(0, int((maximo - minimo).total_seconds())))
        else:
            dia = now_cr.date() + timedelta(days=rng.randint(1, 6))
            fin = _cr(dia, rng.randint(8 * 60, 18 * 60))
        lo, hi = now - timedelta(days=2), now - timedelta(hours=1)
        inicio = lo + timedelta(seconds=rng.randint(0, int((hi - lo).total_seconds())))
        veh = placas[i]["vehiculo_id"]
        monto, desglose = cotizar(precios[veh], inicio, fin)
        rentas.append(dict(
            placa_id=placas[i]["id"], vehiculo_id=veh, usuario_id=usuario(), inicio=inicio,
            fin_programado=fin, fin_real=None, monto=monto, desglose=desglose, estado="activa",
            ubicacion_recibida=None, recibida_por=None, recibida_en=None,
        ))
        ocupado[i].append((inicio, fin))
        final[i].update(estado="Rentada", fecha=fin)

    # Vencidas sin recibir: terminaron ayer (día CR)
    ayer = now_cr.date() - timedelta(days=1)
    for i in vencidas:
        fin = _cr(ayer, rng.randint(9 * 60, 17 * 60))
        inicio = fin - timedelta(hours=rng.choice([5, 24, 48]))
        veh = placas[i]["vehiculo_id"]
        monto, desglose = cotizar(precios[veh], inicio, fin)
        rentas.append(dict(
            placa_id=placas[i]["id"], vehiculo_id=veh, usuario_id=usuario(), inicio=inicio,
            fin_programado=fin, fin_real=fin, monto=monto, desglose=desglose,
            estado="vencida_sin_recibir", ubicacion_recibida=None, recibida_por=None,
            recibida_en=None,
        ))
        ocupado[i].append((inicio, fin))
        final[i].update(estado="Disponible", ub=NO_ACTUALIZADA, fecha=None)

    for i in fuera:
        final[i].update(estado="Fuera de Servicio", ub="Taller Nico", fecha=None)
    for i in resto:
        final[i]["ub"] = rng.choice(UBICACIONES_DISPONIBLES)

    # ---- 2. Historial finalizado (últimos 12 meses, nunca después de now - 1 día) ----
    limite = now - timedelta(days=1)
    primer_dia = (now_cr - timedelta(days=365)).date()
    dias = [primer_dia + timedelta(days=k) for k in range(365)]
    pesos_dia = [_peso_mes(d.month) for d in dias]
    pesos_veh = [PESOS_CATEGORIA.get(v["categoria"], 1) for v in vehiculos]
    n_hist = intentos = 0
    while n_hist < HISTORICAS and intentos < 50000:
        intentos += 1
        v = rng.choices(vehiculos, weights=pesos_veh)[0]
        pv = precios[v["id"]]
        if not pv or not por_vehiculo[v["id"]]:
            continue
        tarifas = sorted(pv)
        tarifa = rng.choices(tarifas, weights=[PESOS_TARIFA.get(t, 1) for t in tarifas])[0]
        dia = rng.choices(dias, weights=pesos_dia)[0]
        if tarifa == "DIA":
            inicio, fin = _cr(dia, 8 * 60 + 30), _cr(dia, 17 * 60)
        else:
            inicio = _cr(dia, 5 * rng.randint(7 * 12, 16 * 12))
            fin = inicio + timedelta(hours=TARIFA_HORAS[tarifa])
        if fin > limite:
            continue
        i = rng.choice(por_vehiculo[v["id"]])
        if any(inicio < f and fin > s for s, f in ocupado[i]):
            continue
        ocupado[i].append((inicio, fin))
        rentas.append(dict(
            placa_id=placas[i]["id"], vehiculo_id=v["id"], usuario_id=None, inicio=inicio,
            fin_programado=fin, fin_real=fin, monto=pv[tarifa], desglose=TARIFA_ETIQUETA[tarifa],
            estado="finalizada", ubicacion_recibida=rng.choice(UBICACIONES_REALES),
            recibida_por=None, recibida_en=fin,
        ))
        n_hist += 1
    # Usuario asignado aparte para no mezclar el azar con los descartes
    for r in rentas:
        if r["usuario_id"] is None:
            r["usuario_id"] = r["recibida_por"] = usuario()

    # ---- Escritura ----
    conn.execute(
        sa.text(
            "UPDATE placas SET placa = :placa, estado = :estado, ubicacion_actual = :ub, "
            "fecha_hora_finalizacion = :fecha WHERE id = :id"
        ),
        [{"id": placas[i]["id"], **f} for i, f in final.items()],
    )
    conn.execute(
        sa.text(
            "INSERT INTO rentas (placa_id, vehiculo_id, usuario_id, inicio, fin_programado, "
            "fin_real, monto, desglose, estado, ubicacion_recibida, recibida_por, recibida_en) "
            "VALUES (:placa_id, :vehiculo_id, :usuario_id, :inicio, :fin_programado, :fin_real, "
            ":monto, :desglose, :estado, :ubicacion_recibida, :recibida_por, :recibida_en)"
        ),
        rentas,
    )

    return {
        "placas_con_numero": len(candidatas),
        "rentas_finalizadas": n_hist,
        "rentadas": len(rentadas),
        "rentadas_hoy": len(hoy),
        "vencidas_sin_recibir": len(vencidas),
        "fuera_de_servicio": len(fuera),
        "disponibles": len(resto),
    }
