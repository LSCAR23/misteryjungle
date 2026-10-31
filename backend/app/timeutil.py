"""Utilidades de tiempo. Costa Rica es UTC-6 fijo (sin horario de verano)."""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

CR = ZoneInfo("America/Costa_Rica")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_cr(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(CR)


def rango_dia_cr(now: datetime) -> tuple[datetime, datetime]:
    """[00:00, 24:00) del día calendario CR que contiene `now`, expresado en UTC."""
    local = to_cr(now)
    inicio = datetime.combine(local.date(), time.min, tzinfo=CR)
    fin = datetime.combine(local.date() + timedelta(days=1), time.min, tzinfo=CR)
    return inicio.astimezone(timezone.utc), fin.astimezone(timezone.utc)


def mes_cr(dt: datetime) -> str:
    return to_cr(dt).strftime("%Y-%m")
