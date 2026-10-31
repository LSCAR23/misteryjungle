"""Métricas del dashboard (PLAN §3). Agregaciones en SQL, meses calendario en hora CR."""
from datetime import datetime, time, timezone

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.enums import Categoria, EstadoPlaca, EstadoRenta, Ubicacion
from app.models import Placa, Renta, Usuario, Vehiculo
from app.timeutil import CR, to_cr

DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
_TZ = "America/Costa_Rica"


def _f(v) -> float:
    return round(float(v or 0), 2)


def _mes_inicio(year: int, month: int) -> datetime:
    """00:00 CR del día 1 de (year, month), en UTC. `month` puede desbordar 12."""
    year += (month - 1) // 12
    month = (month - 1) % 12 + 1
    return datetime.combine(datetime(year, month, 1).date(), time.min, tzinfo=CR).astimezone(
        timezone.utc
    )


def calcular(db: Session, now: datetime, meses: int = 12) -> dict:
    local = to_cr(now)
    # (año, mes 1..12) de los últimos `meses` meses CR, incluyendo el actual
    idx = local.year * 12 + (local.month - 1)
    ym = [(i // 12, i % 12 + 1) for i in range(idx - meses + 1, idx + 1)]
    keys = [f"{y:04d}-{m:02d}" for y, m in ym]
    desde = _mes_inicio(*ym[0])
    hasta = _mes_inicio(ym[-1][0], ym[-1][1] + 1)

    en_rango = [Renta.inicio >= desde, Renta.inicio < hasta]
    local_inicio = sa.func.timezone(_TZ, Renta.inicio)
    mes_expr = sa.func.to_char(local_inicio, "YYYY-MM")
    n = sa.func.count(Renta.id)
    ing = sa.func.coalesce(sa.func.sum(Renta.monto), 0)

    # --- por mes ---
    filas = db.execute(sa.select(mes_expr, n, ing).where(*en_rango).group_by(mes_expr)).all()
    mapa = {r[0]: (int(r[1]), _f(r[2])) for r in filas}
    por_mes = [
        {"mes": k, "rentas": mapa.get(k, (0, 0.0))[0], "ingresos": mapa.get(k, (0, 0.0))[1]}
        for k in keys
    ]

    # --- por vehículo ---
    nombre_v = Vehiculo.marca + sa.literal(" ") + Vehiculo.modelo
    filas = db.execute(
        sa.select(Vehiculo.id, nombre_v, Vehiculo.categoria, n, ing)
        .join(Vehiculo, Vehiculo.id == Renta.vehiculo_id)
        .where(*en_rango)
        .group_by(Vehiculo.id, Vehiculo.marca, Vehiculo.modelo, Vehiculo.categoria)
    ).all()
    por_vehiculo = [
        {
            "vehiculo": r[1],
            "categoria": Categoria(r[2]).value,
            "rentas": int(r[3]),
            "ingresos": _f(r[4]),
        }
        for r in filas
    ]
    por_vehiculo.sort(key=lambda x: (-x["ingresos"], -x["rentas"], x["vehiculo"]))

    # --- por categoría ---
    filas = db.execute(
        sa.select(Vehiculo.categoria, n, ing)
        .join(Vehiculo, Vehiculo.id == Renta.vehiculo_id)
        .where(*en_rango)
        .group_by(Vehiculo.categoria)
    ).all()
    por_categoria = [
        {"categoria": Categoria(r[0]).value, "rentas": int(r[1]), "ingresos": _f(r[2])}
        for r in filas
    ]
    por_categoria.sort(key=lambda x: (-x["ingresos"], -x["rentas"], x["categoria"]))

    # --- por usuario ---
    filas = db.execute(
        sa.select(Usuario.id, Usuario.username, n, ing)
        .join(Usuario, Usuario.id == Renta.usuario_id)
        .where(*en_rango)
        .group_by(Usuario.id, Usuario.username)
    ).all()
    por_usuario = [{"usuario": r[1], "rentas": int(r[2]), "ingresos": _f(r[3])} for r in filas]
    por_usuario.sort(key=lambda x: (-x["rentas"], -x["ingresos"], x["usuario"]))

    # --- por día de semana (inicio en CR) ---
    dow = sa.cast(sa.extract("isodow", local_inicio), sa.Integer)
    filas = db.execute(sa.select(dow, n).where(*en_rango).group_by(dow)).all()
    dmap = {int(r[0]): int(r[1]) for r in filas}
    por_dia_semana = [{"dia": d, "rentas": dmap.get(i + 1, 0)} for i, d in enumerate(DIAS)]

    # --- promedios ---
    dur_h = sa.func.extract("epoch", Renta.fin_programado - Renta.inicio) / 3600
    prom = db.execute(
        sa.select(sa.func.avg(dur_h), sa.func.avg(Renta.monto)).where(*en_rango)
    ).one()

    # --- unidades ---
    est = {
        EstadoPlaca(k): int(v)
        for k, v in db.execute(
            sa.select(Placa.estado, sa.func.count(Placa.id)).group_by(Placa.estado)
        ).all()
    }
    total = sum(est.values())
    rentadas = est.get(EstadoPlaca.RENTADA, 0)
    fuera = est.get(EstadoPlaca.FUERA_DE_SERVICIO, 0)
    base = total - fuera
    ocupacion = round(rentadas / base, 4) if base > 0 else 0.0

    # --- pendientes por recibir ---
    vencidas = db.scalar(
        sa.select(sa.func.count(Renta.id)).where(Renta.estado == EstadoRenta.VENCIDA_SIN_RECIBIR)
    )
    sin_ubic = db.scalar(
        sa.select(sa.func.count(Placa.id)).where(
            Placa.ubicacion_actual == Ubicacion.NO_ACTUALIZADA,
            Placa.estado != EstadoPlaca.RENTADA,
            ~sa.exists().where(
                Renta.placa_id == Placa.id, Renta.estado == EstadoRenta.VENCIDA_SIN_RECIBIR
            ),
        )
    )

    # --- disponibles por ubicación ---
    filas = db.execute(
        sa.select(Placa.ubicacion_actual, sa.func.count(Placa.id))
        .where(Placa.estado == EstadoPlaca.DISPONIBLE)
        .group_by(Placa.ubicacion_actual)
    ).all()
    disp = [{"ubicacion": Ubicacion(r[0]).value, "disponibles": int(r[1])} for r in filas]
    disp.sort(key=lambda x: (-x["disponibles"], x["ubicacion"]))

    # --- destacados ---
    hay = bool(por_vehiculo)
    pop = max(por_vehiculo, key=lambda x: (x["rentas"], x["ingresos"])) if hay else None
    mas_ing = por_vehiculo[0] if hay else None
    usr = por_usuario[0] if por_usuario else None
    mes_top = (
        max((m for m in por_mes if m["rentas"] > 0), key=lambda x: (x["ingresos"], x["rentas"]))
        if hay
        else None
    )

    actual = por_mes[-1]
    if len(por_mes) > 1:
        ingresos_ant = por_mes[-2]["ingresos"]
    else:  # meses == 1: el mes previo queda fuera del rango, se consulta aparte
        ingresos_ant = _f(
            db.scalar(
                sa.select(ing).where(
                    Renta.inicio >= _mes_inicio(ym[0][0], ym[0][1] - 1), Renta.inicio < desde
                )
            )
        )

    return {
        "kpis": {
            "ingresos_mes_actual": actual["ingresos"],
            "ingresos_mes_anterior": ingresos_ant,
            "rentas_mes_actual": actual["rentas"],
            "ocupacion_actual": float(ocupacion),
            "unidades_total": total,
            "unidades_rentadas": rentadas,
            "unidades_fuera_servicio": fuera,
            "pendientes_recibir": int(vencidas or 0) + int(sin_ubic or 0),
            "duracion_promedio_horas": _f(prom[0]),
            "ticket_promedio": _f(prom[1]),
        },
        "vehiculo_mas_popular": (
            {"vehiculo": pop["vehiculo"], "rentas": pop["rentas"]} if pop else None
        ),
        "vehiculo_mas_ingresos": (
            {"vehiculo": mas_ing["vehiculo"], "ingresos": mas_ing["ingresos"]} if mas_ing else None
        ),
        "usuario_top": usr,
        "mes_top": dict(mes_top) if mes_top else None,
        "por_mes": por_mes,
        "por_vehiculo": por_vehiculo,
        "por_categoria": por_categoria,
        "por_usuario": por_usuario,
        "por_dia_semana": por_dia_semana,
        "disponibles_por_ubicacion": disp,
    }
