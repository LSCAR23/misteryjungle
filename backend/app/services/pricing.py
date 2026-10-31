"""Cálculo de la tarifa óptima por duración (PLAN §4). Función pura, sin BD."""
from collections.abc import Mapping
from datetime import datetime, time
from decimal import ROUND_HALF_UP, Decimal
from math import ceil
from zoneinfo import ZoneInfo

from app.enums import TARIFA_ETIQUETA, TARIFA_HORAS, Tarifa

CR = ZoneInfo("America/Costa_Rica")
TOLERANCIA_MIN = 15
LIMITE_DIA = time(17, 30)
CENT = Decimal("0.01")


def _dec(valor) -> Decimal:
    # str() evita arrastrar el error binario de los float.
    return valor if isinstance(valor, Decimal) else Decimal(str(valor))


def cotizar(
    precios: Mapping[str, Decimal | float | int], inicio: datetime, fin: datetime
) -> tuple[Decimal, str]:
    """Devuelve (monto, desglose) de la combinación más barata que cubre la duración."""
    if inicio.tzinfo is None or fin.tzinfo is None:
        raise ValueError("inicio y fin deben incluir zona horaria")
    if fin <= inicio:
        raise ValueError("La fecha de fin debe ser posterior al inicio")

    # Se normalizan las claves por si llegan como Tarifa (str, Enum).
    p = {(k.value if isinstance(k, Tarifa) else str(k)): _dec(v) for k, v in precios.items()}

    # 1. Minutos (techo) y tolerancia de 15 min.
    minutos = ceil((fin - inicio).total_seconds() / 60)
    horas = max(1, ceil((minutos - TOLERANCIA_MIN) / 60))

    # 2. Tarifas por horas aplicables, de mayor a menor duración
    #    (con empate de costo se prefiere la de mayor duración).
    tarifas = sorted(
        ((c, TARIFA_HORAS[c], p[c]) for c in TARIFA_HORAS if c in p),
        key=lambda t: -t[1],
    )

    mejor: tuple[Decimal, dict[str, int]] | None = None
    if tarifas:
        # 3. Mochila no acotada: costo[h] = mínimo para cubrir al menos h horas.
        costo: list[Decimal] = [Decimal(0)] * (horas + 1)
        elegida: list[str | None] = [None] * (horas + 1)
        for h in range(1, horas + 1):
            for codigo, dur, precio in tarifas:
                c = costo[max(0, h - dur)] + precio
                if elegida[h] is None or c < costo[h]:
                    costo[h] = c
                    elegida[h] = codigo
        conteos: dict[str, int] = {}
        h = horas
        while h > 0:
            codigo = elegida[h]
            conteos[codigo] = conteos.get(codigo, 0) + 1
            h = max(0, h - TARIFA_HORAS[codigo])
        mejor = (costo[horas], conteos)

    # 4. Candidato DIA: mismo día calendario CR y fin <= 17:30 CR. Empate -> DIA.
    if Tarifa.DIA.value in p:
        li, lf = inicio.astimezone(CR), fin.astimezone(CR)
        if li.date() == lf.date() and lf.time() <= LIMITE_DIA:
            if mejor is None or p[Tarifa.DIA.value] <= mejor[0]:
                mejor = (p[Tarifa.DIA.value], {Tarifa.DIA.value: 1})

    if mejor is None:
        raise ValueError("El vehículo no tiene una tarifa aplicable para esta duración")

    total, conteos = mejor

    # 5. Desglose: de mayor a menor duración.
    piezas = []
    for codigo in sorted(conteos, key=lambda c: TARIFA_HORAS.get(c, 0), reverse=True):
        n = conteos[codigo]
        etiqueta = TARIFA_ETIQUETA[codigo]
        piezas.append(etiqueta if n == 1 else f"{n} × {etiqueta}")

    return total.quantize(CENT, rounding=ROUND_HALF_UP), " + ".join(piezas)
