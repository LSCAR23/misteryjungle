"""Enums del dominio (valores exactos según PLAN §2)."""
from enum import Enum


class Categoria(str, Enum):
    SCOOTER = "Scooter"
    MOTO = "Moto"
    ATV = "ATV"
    UTV = "UTV"
    CAMION = "Camion"


class Ubicacion(str, Enum):
    PLAYA_CHIQUITA = "Playa Chiquita"
    PUERTO_VIEJO = "Puerto Viejo"
    PLAYA_NEGRA = "Playa Negra"
    B_AZUL = "B.Azul"
    TALLER_NICO = "Taller Nico"
    # Sólo la asigna el sistema al vencer una renta; no aparece en selects.
    NO_ACTUALIZADA = "Ubicación no actualizada"


# Las 5 ubicaciones "reales" (seleccionables por el usuario).
UBICACIONES_REALES = (
    Ubicacion.PLAYA_CHIQUITA,
    Ubicacion.PUERTO_VIEJO,
    Ubicacion.PLAYA_NEGRA,
    Ubicacion.B_AZUL,
    Ubicacion.TALLER_NICO,
)


class EstadoPlaca(str, Enum):
    RENTADA = "Rentada"
    DISPONIBLE = "Disponible"
    FUERA_DE_SERVICIO = "Fuera de Servicio"


class Rol(str, Enum):
    ADMIN = "admin"
    EMPLEADO = "empleado"


class Tarifa(str, Enum):
    CINCO_HORAS = "5H"
    DIA = "DIA"
    VEINTICUATRO_HORAS = "24H"
    DOS_DIAS = "2D"
    TRES_DIAS = "3D"
    SEMANA = "1S"
    DIEZ_DIAS = "10D"
    MES = "MES"


class EstadoRenta(str, Enum):
    ACTIVA = "activa"
    VENCIDA_SIN_RECIBIR = "vencida_sin_recibir"
    FINALIZADA = "finalizada"


# Horas que cubre cada tarifa (DIA es especial: depende del horario, se excluye).
TARIFA_HORAS = {
    Tarifa.CINCO_HORAS.value: 5,
    Tarifa.VEINTICUATRO_HORAS.value: 24,
    Tarifa.DOS_DIAS.value: 48,
    Tarifa.TRES_DIAS.value: 72,
    Tarifa.SEMANA.value: 168,
    Tarifa.DIEZ_DIAS.value: 240,
    Tarifa.MES.value: 720,
}

# Etiquetas en español para el desglose.
TARIFA_ETIQUETA = {
    Tarifa.CINCO_HORAS.value: "5 horas",
    Tarifa.DIA.value: "Día (8am–5:30pm)",
    Tarifa.VEINTICUATRO_HORAS.value: "24 horas",
    Tarifa.DOS_DIAS.value: "2 días",
    Tarifa.TRES_DIAS.value: "3 días",
    Tarifa.SEMANA.value: "1 semana",
    Tarifa.DIEZ_DIAS.value: "10 días",
    Tarifa.MES.value: "Mes",
}
