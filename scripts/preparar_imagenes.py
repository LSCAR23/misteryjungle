"""Prepara las fotos sin fondo de `imagenes_vehiculos/` para la app.

Recorta el espacio transparente, deja un margen, limita el ancho a 800 px y guarda
cada imagen como `frontend/public/vehiculos/<slug>.png` (el nombre que espera la app).

Uso: python scripts/preparar_imagenes.py
"""
import re
import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
ORIGEN = RAIZ / "imagenes_vehiculos"
DESTINO = RAIZ / "frontend" / "public" / "vehiculos"

# Palabra clave en el nombre del archivo (minúsculas) -> slug del vehículo. El orden importa.
REGLAS = [
    (r"deluxe|crew", "honda-pioneer-deluxe-crew"),
    (r"pioneer", "honda-pioneer-4x4"),
    (r"talon.*(4wd|-4\b|x-4|4 ?plazas|4seat)", "honda-talon-4wd"),
    (r"talon", "honda-talon-4x4"),
    (r"rincon", "honda-rincon-4x4"),
    (r"trx|rancher|fourtrax", "honda-trx-4x4"),
    (r"crf ?300|rally", "honda-crf300-rally"),
    (r"crf ?250", "honda-crf250"),
    (r"xr ?190", "honda-xr190"),
    (r"cbf|cb ?150", "honda-cbf150s"),
    (r"elite", "honda-elite"),
    (r"navi", "honda-navi"),
    (r"isuzu|camion|camión|truck|serie ?q", "isuzu-serie-q"),
]

ANCHO_MAX = 800
MARGEN = 0.04


def slug_para(nombre: str) -> str | None:
    n = nombre.lower()
    for patron, slug in REGLAS:
        if re.search(patron, n):
            return slug
    return None


def preparar(origen: Path, destino: Path) -> None:
    im = Image.open(origen).convert("RGBA")
    caja = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if caja:
        im = im.crop(caja)
    m = int(max(im.size) * MARGEN)
    lienzo = Image.new("RGBA", (im.width + 2 * m, im.height + 2 * m), (0, 0, 0, 0))
    lienzo.paste(im, (m, m))
    if lienzo.width > ANCHO_MAX:
        alto = round(lienzo.height * ANCHO_MAX / lienzo.width)
        lienzo = lienzo.resize((ANCHO_MAX, alto), Image.LANCZOS)
    lienzo.save(destino, optimize=True)


def main() -> int:
    DESTINO.mkdir(parents=True, exist_ok=True)
    sin_asignar = []
    for archivo in sorted(ORIGEN.glob("*.png")):
        slug = slug_para(archivo.name)
        if not slug:
            sin_asignar.append(archivo.name)
            continue
        salida = DESTINO / f"{slug}.png"
        preparar(archivo, salida)
        print(f"{archivo.name}  ->  {salida.relative_to(RAIZ)}  ({salida.stat().st_size // 1024} KB)")
    for nombre in sin_asignar:
        print(f"SIN ASIGNAR (renómbralo con el modelo): {nombre}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
