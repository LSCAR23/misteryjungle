"""Catálogo inicial de vehículos (PLAN §5).

Datos planos: no importa nada de app.models. Cada dict corresponde a una fila
de la tabla de §5. `precios` sólo contiene las tarifas con valor (las "—" se omiten).
"""

UBICACIONES_INICIALES = ["Puerto Viejo", "Playa Chiquita", "Playa Negra", "B.Azul"]

CATALOGO: list[dict] = [
    {
        "slug": "honda-navi",
        "marca": "Honda",
        "modelo": "Navi",
        "categoria": "Scooter",
        "cilindrada": 109,
        "unidades": 6,
        "precios": {"DIA": 30, "5H": 20, "24H": 35, "2D": 60, "3D": 80, "1S": 175, "10D": 200, "MES": 500},
    },
    {
        "slug": "honda-elite",
        "marca": "Honda",
        "modelo": "Elite 125",
        "categoria": "Scooter",
        "cilindrada": 124,
        "unidades": 4,
        "precios": {"DIA": 30, "5H": 20, "24H": 35, "2D": 60, "3D": 80, "1S": 175, "10D": 200, "MES": 500},
    },
    {
        "slug": "honda-cbf150s",
        "marca": "Honda",
        "modelo": "CBF150S",
        "categoria": "Moto",
        "cilindrada": 149,
        "unidades": 2,
        "precios": {"DIA": 40, "5H": 30, "24H": 50, "2D": 90, "3D": 130, "1S": 250, "10D": 300, "MES": 600},
    },
    {
        "slug": "honda-xr190",
        "marca": "Honda",
        "modelo": "XR190",
        "categoria": "Moto",
        "cilindrada": 184,
        "unidades": 4,
        "precios": {"DIA": 40, "5H": 30, "24H": 50, "2D": 90, "3D": 130, "1S": 250, "10D": 300, "MES": 600},
    },
    {
        "slug": "honda-crf250",
        "marca": "Honda",
        "modelo": "CRF250",
        "categoria": "Moto",
        "cilindrada": 250,
        "unidades": 3,
        "precios": {"DIA": 50, "5H": 40, "24H": 70, "2D": 130, "3D": 190, "1S": 350, "10D": 450, "MES": 1000},
    },
    {
        "slug": "honda-crf300-rally",
        "marca": "Honda",
        "modelo": "CRF300 Rally",
        "categoria": "Moto",
        "cilindrada": 286,
        "unidades": 4,
        "precios": {"DIA": 50, "24H": 80, "2D": 140, "3D": 200, "1S": 360, "10D": 460, "MES": 1100},
    },
    {
        "slug": "honda-trx-4x4",
        "marca": "Honda",
        "modelo": "TRX 420 4x4",
        "categoria": "ATV",
        "cilindrada": 420,
        "unidades": 4,
        "precios": {"DIA": 60, "5H": 50, "24H": 80, "2D": 155, "3D": 225, "1S": 490, "10D": 600, "MES": 1300},
    },
    {
        "slug": "honda-rincon-4x4",
        "marca": "Honda",
        "modelo": "Rincon 4x4",
        "categoria": "ATV",
        "cilindrada": 675,
        "unidades": 6,
        "precios": {"DIA": 80, "24H": 100, "2D": 180, "3D": 240, "1S": 520, "10D": 700, "MES": 1500},
    },
    {
        "slug": "honda-pioneer-4x4",
        "marca": "Honda",
        "modelo": "Pioneer 4x4",
        "categoria": "UTV",
        "cilindrada": 675,
        "unidades": 5,
        "precios": {"DIA": 150, "24H": 200, "2D": 350, "3D": 450, "1S": 850, "10D": 1000, "MES": 2500},
    },
    {
        "slug": "honda-pioneer-deluxe-crew",
        "marca": "Honda",
        "modelo": "Pioneer Deluxe Crew",
        "categoria": "UTV",
        "cilindrada": 999,
        "unidades": 3,
        "precios": {"DIA": 150, "24H": 200, "2D": 350, "3D": 450, "1S": 850, "10D": 1000, "MES": 2500},
    },
    {
        "slug": "honda-talon-4x4",
        "marca": "Honda",
        "modelo": "Talon 4x4",
        "categoria": "UTV",
        "cilindrada": 999,
        "unidades": 4,
        "precios": {"24H": 250, "2D": 400, "3D": 500, "1S": 900, "10D": 1100, "MES": 2700},
    },
    {
        "slug": "honda-talon-4wd",
        "marca": "Honda",
        "modelo": "Talon 4WD (4 plazas)",
        "categoria": "UTV",
        "cilindrada": 999,
        "unidades": 2,
        "precios": {"24H": 300, "2D": 500, "3D": 600, "1S": 1000, "10D": 1200, "MES": 2800},
    },
    {
        "slug": "isuzu-serie-q",
        "marca": "Isuzu",
        "modelo": "Serie Q",
        "categoria": "Camion",
        "cilindrada": 5193,
        "unidades": 1,
        "precios": {"DIA": 150, "5H": 100, "24H": 200, "2D": 300, "3D": 450, "1S": 850, "10D": 1000},
    },
]

for _v in CATALOGO:
    _v["imagen"] = f"/vehiculos/{_v['slug']}.png"
del _v
